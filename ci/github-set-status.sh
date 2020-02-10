#!/usr/bin/env bash

while getopts ":s:d:c:" opt; do
  case ${opt} in
    s)
      state=$OPTARG
      ;;
    d)
      desc=$OPTARG
      ;;
    c)
      context=$OPTARG
    ;;
    \? )
      echo "Usage: cmd [-s state] [-d description] [-c context]"
      ;;
    : )
      echo "Invalid option: $OPTARG requires an argument" 1>&2
      ;;
  esac
done
shift $((OPTIND -1))

curl -H "Authorization: token ${GITHUB_API_TOKEN}" --data '{"state" : "'"${state}"'", "target_url" : "'"${CI_PROJECT_URL}"'/pipelines/'"${CI_PIPELINE_ID}"'", "description" : "'"${desc}"'", "context" : "'"${context}"'"}' ${GITHUB_REPO_API_URL}/statuses/${CI_COMMIT_SHA}



