# -*- coding: utf-8 -*-

import typing
import json
import boto3
import logging

from ask_sdk_model import RequestEnvelope
from boto3.session import ResourceNotExistsError
from ask_sdk_core.attributes_manager import AbstractPersistenceAdapter
from ask_sdk_core.exceptions import PersistenceException
from ask_sdk_runtime.exceptions import AskSdkException
from os.path import join
from datetime import datetime

from .ObjectKeyGenerators import userId


if typing.TYPE_CHECKING:
    from typing import Callable, Dict
    from ask_sdk_core.handler_input import HandlerInput
    from ask_sdk_model import RequestEnvelope
    from boto3.resources.base import ServiceResource


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class S3PersistenceAdapter(AbstractPersistenceAdapter):
    def __init__(self, bucket_name, object_generator, s3_client=boto3.client('s3'), path_prefix=None):
        self.bucket_name = bucket_name
        self.s3_client = s3_client
        self.object_generator = object_generator
        self.path_prefix = path_prefix if path_prefix else ''

    def get_attributes(self, request_envelope):
        objectId = join(self.path_prefix, self.object_generator(request_envelope))

        try:
            data = self.s3_client.get_object(Bucket=self.bucket_name, Key=objectId)
        except ResourceNotExistsError:
            raise PersistenceException(f'Object {self.bucket_name} and key {objectId} do not exist')
        except Exception as e:
            # Creating an empty file anyways to avoid errors
            self.save_attributes(request_envelope, {'created': datetime.utcnow().isoformat()})
            logger.info(f'ObjectID GET: {objectId}')
            data = self.s3_client.get_object(Bucket=self.bucket_name, Key=objectId)
            # raise AskSdkException(f'GET_ATTRS - There has been some error - {type(e).__name__} - {str(e)}')

        try:
            body_object = json.loads(data['Body'].read().decode('utf-8'))
        except Exception as e:
            raise AskSdkException(f'Could not parse Bucket Resource Body as JSON for Object {self.bucket_name} and key {objectId} do not exist')

        return body_object

    def save_attributes(self, request_envelope, attributes):
        objectId = join(self.path_prefix, self.object_generator(request_envelope))

        logger.info(f'ObjectID SAVE: {objectId}')

        try:
            data = bytes(json.dumps(attributes), 'utf-8')
        except ResourceNotExistsError:
            raise AskSdkException(f'Could not convert object to bytes {self.bucket_name} and key {objectId} do not exist')
        except Exception as e:
            raise AskSdkException(f'There has been some error - {type(e).__name__} - {str(e)}')

        try:
            response = self.s3_client.put_object(Bucket=self.bucket_name, Key=objectId, Body=data)
        except Exception as e:
            raise PersistenceException(f'Could put object {self.bucket_name} and key {objectId} do not exist - {type(e).__name__} - {str(e)}')
