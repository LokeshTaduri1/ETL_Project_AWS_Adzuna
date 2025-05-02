{
  "Comment": "ETL Workflow using AWS Glue Jobs",
  "StartAt": "ExtractDataFromAPI",
  "States": {
    "ExtractDataFromAPI": {
      "Type": "Task",
      "Resource": "arn:aws:states:::glue:startJobRun.sync",
      "Parameters": {
        "JobName": "data-extraction-job"
      },
      "Next": "TransformData",
      "ResultPath": "$.s3ObjectKeyExtract",
      "Catch": [
        {
          "ErrorEquals": [
            "States.ALL"
          ],
          "Next": "FailureState"
        }
      ]
    },
    "TransformData": {
      "Type": "Task",
      "Resource": "arn:aws:states:::glue:startJobRun.sync",
      "Parameters": {
        "JobName": "data-Transformation-job",
        "Arguments": {
          "--s3ObjectKey": "$.s3ObjectKeyExtract"
        }
      },
      "Next": "LoadDataToRedshift",
      "ResultPath": "$.s3ObjectKeyTransformed",
      "Catch": [
        {
          "ErrorEquals": [
            "States.ALL"
          ],
          "Next": "FailureState"
        }
      ]
    },
    "LoadDataToRedshift": {
      "Type": "Task",
      "Resource": "arn:aws:states:::glue:startJobRun.sync",
      "Parameters": {
        "JobName": "data-loading-job",
        "Arguments": {
          "--s3ObjectKeyTransformed": "$.s3ObjectKeyTransformed"
        }
      },
      "End": true,
      "Catch": [
        {
          "ErrorEquals": [
            "States.ALL"
          ],
          "Next": "FailureState"
        }
      ]
    },
    "FailureState": {
      "Type": "Fail",
      "Cause": "An error occurred in the ETL process"
    }
  }
}