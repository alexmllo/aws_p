import subprocess
import boto3
import logging
import psycopg
from botocore.config import Config
from psycopg import OperationalError
import time
import argparse
from datetime import datetime, timedelta
import urllib.parse
import sys
from os import getenv

my_config = Config(
    region_name="ap-south-1",
    signature_version="v4",
    retries={"max_attempts": 10, "mode": "standard"},
)

ec2_client = boto3.client("ec2", config=my_config)
rds = boto3.client("rds", config=my_config)
s3_client = boto3.client("s3", config=my_config)
ssm = boto3.client("ssm", config=my_config)
cloudwatch = boto3.client("cloudwatch", config=my_config)

def source_rds_instance(dbinstance):
    return rds.describe_db_instances(DBIntanceIdentifier=dbinstance)["DBInstances"][0]

def get_db_freestorage(DBInstanceIdentifier):
    response = cloudwatch.get_metric_data(
        MetricDataQueries=[
            {
                "Id": "fetching_FreeStorageSpace",
                "MetricStat": {
                    "Metric": {
                        "Namespace": "AWS/RDS",
                        "MetricName": "FreeStorageSpace",
                        "Dimensions": [
                            {
                                "Name": "DBInstanceIdentifier",
                                "Value": DBInstanceIdentifier,
                            }
                        ],
                    },
                    "Period": 86400 * 7,
                    "Stat": "Minimum",
                },
            }
        ],
        StartTime=(datetime.now() - timedelta(seconds=86400 * 7)).timestamp(),
        EndTime=datetime.now().timestamp(),
        ScanBy="TimestampDescending",
    )
    return round(response["MetricDataResults"][0]["Values"][0] / 1024**3, 2)

def evaluate_rds(dbinstance):
    free_storage = get_db_freestorage(dbinstance)
    allocated_storage = source_rds_instance(dbinstance)["AllocatedStorage"]

    return f" RDS instance {dbinstance} is allocated {allocated_storage} GB and out of that, {free_storage} GB is available"

def get_db_details(dbinstance):
    paramreter_name = f"/database/{dbinstance}"
    response = ssm.get_parameter(Name=paramreter_name, WithDecryption=True | False)["Parameter"]["Value"]

    user = response.split(":")[1].split("/")[-1]
    password = response.split(":")[2].split("@")[0]
    db = response.split("/")[-1]
    host = response.split(":")[2].split("@")[-1]
    port = response.split(":")[3].split("/")[0]

    return host, db, user, password, port

def duplicate_rds(dbinstance: str, new_allocated_storage: int) -> dict:
    source_rds_data = source_rds_instance(dbinstance)
    _, db, user, password, port = get_db_details(dbinstance)

    instance_params = {
        "DBName": db,
        "DBInstanceIdentifier": f"{source_rds_data['DBInstanceIdentifier']}new",
        "AllocatedStorage": new_allocated_storage,
        "DBInstanceClass": source_rds_data["DBInstanceClass"],
        "Engine": source_rds_data["Engine"],
        "MasterUsername": user,
        "MasterUserPassword": password,
        "Port": int(port),
        "DBSecurityGroups": [
            items["DBSecurityGroupName"]
            for items in source_rds_data["DBSecurityGroups"]
        ],
        "VpcSecurityGroupIds": [
            items["VpcSecurityGroupId"]
            for items in source_rds_data["VpcSecurityGroups"]
        ],
        "AvailabilityZone": source_rds_data["AvailabilityZone"],
        "DBSubnetGroupName": source_rds_data["DBSubnetGroup"]["DBSubnetGroupName"],
        "PreferredMaintenanceWindow": source_rds_data["PreferredMaintenanceWindow"],
        "DBParameterGroupName": source_rds_data["DBParameterGroups"][0][
            "DBParameterGroupName"
        ],
        "BackupRetentionPeriod": source_rds_data["BackupRetentionPeriod"],
        "PreferredBackupWindow": source_rds_data["PreferredBackupWindow"],
        "MultiAZ": source_rds_data["MultiAZ"],
        "EngineVersion": source_rds_data["EngineVersion"],
        "AutoMinorVersionUpgrade": source_rds_data["AutoMinorVersionUpgrade"],
        "LicenseModel": source_rds_data["LicenseModel"],
        "OptionGroupName": source_rds_data["OptionGroupMemberships"][0][
            "OptionGroupName"
        ],
        "PubliclyAccessible": source_rds_data["PubliclyAccessible"],
        "Tags": source_rds_data["TagList"],
        "StorageType": source_rds_data["StorageType"],
        "StorageEncrypted": source_rds_data["StorageEncrypted"],
        "KmsKeyId": source_rds_data["KmsKeyId"],
        "CopyTagsToSnapshot": source_rds_data["CopyTagsToSnapshot"],
        "EnableIAMDatabaseAuthentication": source_rds_data[
            "IAMDatabaseAuthenticationEnabled"
        ],
        "EnablePerformanceInsights": source_rds_data["PerformanceInsightsEnabled"],
        "DeletionProtection": source_rds_data["DeletionProtection"],
        "EnableCustomerOwnedIp": source_rds_data["CustomerOwnedIpEnabled"],
        "BackupTarget": source_rds_data["BackupTarget"],
        "NetworkType": source_rds_data["NetworkType"],
        "CACertificateIdentifier": source_rds_data["CACertificateIdentifier"],
    }

    try:
        if source_rds_data["MaxAllocatedStorage"]:
            instance_params["MaxAllocatedStorage"] = source_rds_data["MaxAllocatedStorage"]
    except KeyError:
        pass

    response = rds.create_db_instance(**instance_params)
    return response

def check_rds_availability(host, port, dbname, user, password):
    while True:
        try:
            conn = psycopg.connect(
                host=host, port=port, dbname=dbname, user=user, password=password
            )

            conn.close()
            time.sleep(30)
            return True
        
        except OperationalError as e:
            logging.error(f"Error connecting to the RDS database {host}: {e}")
            logging.info("Retrying in 60 seconds...")
            time.sleep(60)

def backup_postgres_db(host, db, port, user, password, dest_file):
    """
    Backup postgres db to a file
    """
    try:
        process = subprocess.Popen(
            [
                "pg_dump",
                f"--dbname=postgresql://{user}:{password}@{host}:{port}/{db}",
                "-Fc",
                "-f",
                dest_file,
                "-v",
            ],
            stdout=subprocess.PIPE,
        )
        output = process.communicate()[0]
        if int(process.returncode) != 0:
            print(f"Command failed. Return code : {process.returncode}")
            exit(1)
        return output
    except Exception as e:
        logging.error(e)
        exit(1)

def restore_postgres_db(host, db, port, user, password, backup_file, verbose):
    """
    Restore postgres db from a file.
    """
    try:
        process = subprocess.Popen(
            [
                "pg_restore",
                "--no-owner",
                f"--dbname=postgresql://{user}:{password}@{host}:{port}/{db}",
                "-v",
                backup_file,
            ],
            stdout=subprocess.PIPE,
        )
        output = process.communicate()[0]
        if int(process.returncode) != 0:
            logging.error(f"Command failed. Return code : {process.returncode}")

        return output
    except Exception as e:
        logging.error(f"Issue with the db restore : {e}")

def rename_rds(old:str, new:str) -> dict:
    try:
        rds.modify_rds_instance(
            DBInstanceIdentifier=old, NewDBInstanceIdentifier=new, ApplyImmediately=True
        )
        time.sleep(120)
        logging.info(f"DB renamed - {new}")
    except Exception as e:
        logging.error(f"Issue with renaming {old} -> {new} : {e}")
        exit(1)

def swap_db(old: str, new: str) -> None:
    logging.info(f"Renaming db: {old} -> {old}-old")
    rename_rds(old, f"{old}-old")
    logging.info(f"Ranaming db: {new} -> {old}")
    rename_rds(new, old)

def stop_rds(dbinstance: str) -> None:
    try:
        logging.info(f"Stopping the RDS instance - {dbinstance}")
        rds.stop_db_instance(
            DBInstanceIdentifier=dbinstance
        )
    except Exception as e:
        logging.info(f"Issue with stopping - {dbinstance} -> e")
        exit(1)

def migrate_rds(dbinstance, new_allocated_storage):
    host, db, user, password, port = get_db_details(dbinstance)
    password = urllib.parse.quote(password)
    source_rds_data = source_rds_instance(dbinstance)
    logging.info(f"Taking pg_dump of {dbinstance}")
    backup_filename = f"{dbinstance}_dump"

    try:
        backup_postgres_db(
            host, db, port, password, backup_filename
        )
    except Exception as e:
        logging.info(e)
    
    logging.info(f"Creating the duplicate rds of {dbinstance}")
    duplicate_rds_intance = duplicate_rds(dbinstance, int(new_allocated_storage))

    new_rds_DBInstanceIdentifier = duplicate_rds_intance["DBInstance"]["DBInstanceIdentifier"]
    logging.info(f"Creating {new_rds_DBInstanceIdentifier}")
    old_db_endpoint = source_rds_data["Endpoint"]["Address"]
    new_db_endpoint = (
        new_rds_DBInstanceIdentifier + "." + ".".join(old_db_endpoint.split(".")[1:])
    )
    check_rds_availability(new_db_endpoint, port, db, user, password)

    logging.info(f"restoring the new db - {new_rds_DBInstanceIdentifier}")
    try:
        restore_postgres_db(
            new_db_endpoint, db, port, user, password, backup_filename
        )
    except Exception as e:
        print(e)
    
    logging.info("Swapping rds")
    swap_db(dbinstance, new_rds_DBInstanceIdentifier)
    logging.info(f"Stopping the {dbinstance}-old")
    stop_rds(f"{dbinstance}-old")