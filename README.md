flask-image-s3-uploader
=======================

Upload/Download images to S3 bucket

Requirements
============

1. python >3.4
2. AWS account

Usage
=====

1. Create a S3 bucket
2. Create a AWS user who has access to your bucket
3. Set your environment variables:
	* AWS_ACCESS_KEY
	* AWS_SECRET_KEY
	* S3_BUCKET
4. run python runserver.py