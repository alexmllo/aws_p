**Problem:**

In a project focused on optimizing cloud expenses across multiple AWS accounts, we identified several RDS PostgreSQL databases that had been over-provisioned, resulting in significant wasted storage capacity. AWS restricts the direct reduction of allocated storage for RDS instances, and even restoring from a snapshot doesn’t allow for a smaller storage size. To address this, each oversized database had to be recreated with adjusted storage, making the task complex and labor-intensive, especially given the scale—over 100 databases.

**Solution:**

To streamline the process, I developed a Python script using the AWS SDK, boto3, to automate the resizing of RDS instances. This solution was packaged in a Docker container, deployed to ECS, and triggered by an AWS Lambda function, enabling efficient and systematic resizing of our databases and a substantial reduction in cloud costs.

Here’s a similar approach to automate this kind of migration in your environment using boto3:

1. Retrieve each RDS instance's details and storage usage with boto3.
2. Use `pg_dump` to back up the database.
3. Create a duplicate RDS instance with the desired storage capacity, appending a "-new" suffix to the name.
4. Wait for the new instance to become fully available.
5. Restore the database to the new instance using `pg_restore`.
6. Swap the names of the original and new databases to complete the migration.
7. Stop the old instance, and after a period, manually delete it to ensure no data loss.