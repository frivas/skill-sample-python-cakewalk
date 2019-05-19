This is a Python version of the Cake Walk Alexa Skill. There is already a NodeJS version of it with a great explanation [here](https://developer.amazon.com/alexa-skills-kit/courses/cake-walk).

There are a few things I would like to point out of this version:

1. There is no official support for S3 in Python’s ASK SDK, so I used one that I wrote sometime ago, you can find it [here](https://github.com/frivas/alexa-s3-persistence-python) with a couple of changes:
	- I had fixed an error in the function that gets the userID from the *handler_input* object.
	- I added support for ApiClient to the S3 Persistence module.
2. The code is not exactly the same as the original sample.
3. I used ASK SDK for Python v1.9.0.
4. I use *pytz* to handle the timezones.
5. Added a couple of loggers (request and response)
6. If you want to use this sample, add an environment variable called *BUCKET_NAME* with the name of the S3 Bucket you would like to use to store the data.
7. You can also use DynamoDB to store the data.

I hope you find this useful.