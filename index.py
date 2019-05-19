# -*- coding: utf-8 -*-

import logging
import os
import pytz
import boto3


from datetime import datetime


from ask_sdk.standard_s3 import StandardSkillBuilder
from ask_sdk_core.api_client import DefaultApiClient
from ask_sdk_core.dispatch_components import (AbstractRequestHandler, AbstractExceptionHandler, AbstractRequestInterceptor, AbstractResponseInterceptor)
from ask_sdk_core.utils import is_request_type, is_intent_name
from ask_sdk_core.utils.request_util import get_slot_value, get_device_id
from ask_sdk_core.handler_input import HandlerInput
from ask_sdk_model import Response
from ask_sdk_core import attributes_manager
from ask_sdk_s3_persistence import S3PersistenceAdapter
from ask_sdk_s3_persistence.ObjectKeyGenerators import userId, applicationId


s3_client = boto3.client('s3')
bucket_name = os.environ['BUCKET_NAME']


ssb = StandardSkillBuilder(bucket_name=bucket_name, object_generator=userId, s3_client=s3_client, api_client=DefaultApiClient())

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class LaunchRequestHandler(AbstractRequestHandler):
	def can_handle(self, handler_input):
		logger.info(f"In LaunchRequest")
		return is_request_type("LaunchRequest")(handler_input)

	def handle(self, handler_input):
		session_attributes = handler_input.attributes_manager.session_attributes

		year = session_attributes.get("year", None)
		month = session_attributes.get("month", None)
		day = session_attributes.get("day", None)

		if bool(year and month and day):
			users_next_age, days_until_next_bday = hasBirthday(handler_input, year, month, day)
			speechText = f"Happy {users_next_age}th birthday!"
			if days_until_next_bday != 0:
				speechText = f"Welcome back. It looks like there are {days_until_next_bday} days until your {users_next_age}th birthday."
			handler_input.response_builder.speak(speechText)
		else:
			speechText = "Hello! Welcome to Cake Walk. When is your birthday?"
			repromptText = "I was born November sixth, two thousand forteen. When were you born?"
			handler_input.response_builder.speak(speechText).ask(repromptText).set_should_end_session(False)

		return handler_input.response_builder.response


class HelpIntentHandler(AbstractRequestHandler):
	def can_handle(self, handler_input):
		return is_intent_name("AMAZON.HelpIntent")(handler_input)

	def handle(self, handler_input):
		speechText = "You can say hello to me! How can I help?"

		return handler_input.response_builder.speak(speechText).ask(speechText).response


class CancelAndStopIntentHandler(AbstractRequestHandler):
	def can_handle(self, handler_input):
		return is_intent_name("AMAZON.CancelIntent")(handler_input) or is_intent_name("AMAZON.StopIntent")(handler_input)

	def handle(self, handler_input):
		speechText = "Goodbye!"

		return handler_input.response_builder.speak(speechText).set_should_end_session(True).response


class SessionEndedRequestHandler(AbstractRequestHandler):
	def can_handle(self, handler_input):
		return is_request_type("SessionEndedRequest")(handler_input)

	def handle(self, handler_input):
		return handler_input.response_builder.response


class AllExceptionHandler(AbstractExceptionHandler):
	def can_handle(self, handler_input, exception):
		return True

	def handle(self, handler_input, exception):
		# Log the exception in CloudWatch
		print(f"~~~~ Error handled: {exception}")

		speechText = "Sorry, I couldn't understand what you said. Please try again."

		return handler_input.response_builder.speak(speechText).ask(speechText).response


class LoadBirthdayInterceptor(AbstractRequestInterceptor):
	def process(self, handler_input):
		# type: (HandlerInput) -> None
		logger.info('In LoadBirthdayInterceptor')
		attr = handler_input.attributes_manager.persistent_attributes

		attr["year"] = attr.get("year", None)
		attr["month"] = attr.get("month", None)
		attr["day"] = attr.get("day", None)

		handler_input.attributes_manager.session_attributes = attr


class CaptureBirthdayIntentHandler(AbstractRequestHandler):
	def can_handle(self, handler_input):
		return is_intent_name("CaptureBirthdayIntent")(handler_input)

	def handle(self, handler_input):
		year = get_slot_value(handler_input, 'year')
		month = get_slot_value(handler_input, 'month')
		day = get_slot_value(handler_input, 'day')

		birthday_attributes = {}
		birthday_attributes["year"] = year
		birthday_attributes["month"] = month
		birthday_attributes["day"] = day
		handler_input.attributes_manager.persistent_attributes = birthday_attributes
		handler_input.attributes_manager.save_persistent_attributes()

		speechText = f"Thanks, I'll remember that your birthday is {month} {day} {year}."

		handler_input.response_builder.speak(speechText).set_should_end_session(False)
		return handler_input.response_builder.response


class RequestLogger(AbstractRequestInterceptor):
    def process(self, handler_input):
        # logger.debug(f'Alexa Request: {handler_input.request_envelope.request}')
        logger.info(f'Alexa Request: {handler_input.request_envelope.request}')


class ResponseLogger(AbstractResponseInterceptor):
    def process(self, handler_input, response):
        # type: (HandlerInput, Response) -> None
        # logger.debug(f'Alexa Response: {response}')
        logger.info(f'Alexa Response: {response}')


def calculate_age(current_datetime, users_bday):
	logger.info(f"In Calculate Age")
	return (current_datetime.year + 1) - users_bday.year - ((current_datetime.month, current_datetime.day) < (users_bday.month, users_bday.day))


def get_users_next_bday(users_bday, current_datetime):
	logger.info(f"In Get Users Next BDAY")
	if (users_bday.month, users_bday.day) > (current_datetime.month, current_datetime.day):
		users_next_bday = users_bday.replace(year=current_datetime.year)
	else:
		users_next_bday = users_bday.replace(year=current_datetime.year + 1)

	return users_next_bday


def hasBirthday(handler_input, year, month, day):
	device_id = get_device_id(handler_input)
	user_preferences_client = handler_input.service_client_factory.get_ups_service()
	user_time_zone = user_preferences_client.get_system_time_zone(device_id)

	# Current datetime
	current_datetime = datetime.now()
	timezone = pytz.timezone(user_time_zone)
	localized_current_datetime = timezone.localize(current_datetime)

	# User's birthday processing
	users_bday_parsed = datetime.strptime(f"{month} {day} {year}", "%B %d %Y")
	users_bday = datetime.combine(users_bday_parsed, current_datetime.time())
	users_next_age = calculate_age(current_datetime, users_bday)
	users_next_bday = get_users_next_bday(users_bday, current_datetime)
	days_until_next_bday = (users_next_bday - current_datetime).days

	return users_next_age, days_until_next_bday
	

ssb.add_request_handler(LaunchRequestHandler())
ssb.add_request_handler(CaptureBirthdayIntentHandler())
ssb.add_request_handler(CancelAndStopIntentHandler())
ssb.add_request_handler(SessionEndedRequestHandler())
ssb.add_request_handler(HelpIntentHandler())

ssb.add_exception_handler(AllExceptionHandler())

ssb.add_global_request_interceptor(RequestLogger())
ssb.add_global_response_interceptor(ResponseLogger())
ssb.add_global_request_interceptor(LoadBirthdayInterceptor())

handler = ssb.lambda_handler()
