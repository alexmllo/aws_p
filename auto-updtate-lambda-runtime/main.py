import boto3
from packaging.version import Version
import argparse

lambda_client = boto3.client('lambda')

# List all Lambda functions in the account
def list_lambda_functions():
    return lambda_client.list_functions().get("Functions", None)

# Get function names and runtimes from lambda function details
def get_name_runtime(lambda_json_list):
    temp = []
    for item in lambda_json_list:
        name = item.get("FunctionName", "")
        runtime = item.get("Runtime", None)
        if runtime:
            temp.append((name, runtime))
    return temp

# Compare two Python runtimes to check if the first is older
def compare_runtime(runtime, runtime_to_compare_with):
    return Version(runtime.split("python")[-1]) < Version(runtime_to_compare_with.split("python")[-1])

# Update runtime of a specific lambda function
def update_runtime(function_name, old_runtime, new_runtime):
    print(f"Updating {function_name} runtime from {old_runtime} to {new_runtime}")
    try:
        lambda_client.updtate_function_configuration(
            FunctionName=function_name,
            Runtime=new_runtime
        )
    except Exception as e:
        print("An error ocurred while updating the runtime")

def run(runtime_to_compare_with):
    data = get_name_runtime(list_lambda_functions() or [])
    temp = []
    for item in data:
        name, runtime = item
        if compare_runtime(runtime, runtime_to_compare_with):
            temp.append(name)
            update_runtime(name, runtime, runtime_to_compare_with)
    if not temp:
        print(f"No functions with runtime older than {runtime_to_compare_with}")

def parse_arguments():
    parser = argparse.ArgumentParser(description="Encrypt unencrypted SQS queues across multiple AWS accounts")
    parser.add_argument("--python_version", "-a", required=True, help="List of AWS accounts IDs")
    return parser.parse_args()

if __name__ == "__main__":
    args = parse_arguments()
    runtime_to_compare_with = args.python_version
    run(runtime_to_compare_with)