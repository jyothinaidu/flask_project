#!/usr/bin/env bash

aws --profile trustmil iam upload-server-certificate --server-certificate-name trustmile_api_cert --certificate-body file://$1 --private-key file://$2
