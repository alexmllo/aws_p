import boto3
import os

# event contains input data
# context contains runtime information
def lambda_handler(event, context):
    s3_client = boto3.client('s3')

    bucket_path = os.getenv("BUCKET_PATH")
    bucket_name = bucket_path.split("/")[0]
    prefix = bucket_path.split(bucket_name + "/")[1]
    
    # Get all files in this path in the s3 bucket
    response = s3_client.list_objects_v2(
        Bucket=bucket_name,
        Prefix=prefix,
        Delimiter="/",
    )['Contents']

    try:
    # Iteration over the elements
    # filename = "filename-$RANDOM_NUMBER-$(date +%Y-%m-%d).txt"
        for obj in response:
            filename_path = obj['Key']
            year = filename_path.split('.txt')[0].split('-')[2]
            month = filename_path.split('.txt')[0].split('-')[3]
            date = filename_path.split('.txt')[0].split('-')[4]
            new_filename = filename_path.split("incoming/")[1]
            new_path = f"{prefix}{year}/{month}/{date}/{new_filename}"

            # Copy object to new path
            s3.client.copy_object(
                Bucket=bucket_name,
                CopySource={'Bucket': bucket_name, 'Key': filename_path},
                Key=new_path
            )
            # Delete the original file
            s3_client.delete_object(
                Bucket=bucket_name,
                Key=filename_path
            )

    except Exception as e:
        print(e)

# Run the function
if __name__ == '__main__':
    lambda_handler("","")
