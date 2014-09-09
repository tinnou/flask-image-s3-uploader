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

Demo
====

Working example on Heroku at [tradesy-image-uploader.herokuapp.com](http://tradesy-image-uploader.herokuapp.com/image)

To upload an image:
<pre>curl -v -i -F file=@"/PATH/TO/FILE/image.png" http://tradesy-image-uploader.herokuapp.com/image</pre>

To retrieve an image:
Copy paste this url in the browser : http://tradesy-image-uploader.herokuapp.com/image/{IMAGE_ID}

e.g: http://tradesy-image-uploader.herokuapp.com/image/2014-09-09/04:18/5cd5a56d-07d4-46c2-b59f-18bed3787334-image.png
