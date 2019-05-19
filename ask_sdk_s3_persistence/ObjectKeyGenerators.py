# -*- coding: utf-8 -*-


import typing
import logging

from ask_sdk_core.exceptions import PersistenceException

if typing.TYPE_CHECKING:
    from ask_sdk_model import RequestEnvelope


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def userId(request_envelope):
    try:
        user_id = request_envelope.context.system.user.user_id
        return user_id
    except AttributeError:
        raise PersistenceException('PartitionKeyGenerators - Cannot retrieve user id from request envelope!')


def deviceId(request_envelope):
    try:
        device_id = request_envelope.context.system.application.device_id
        return device_id
    except AttributeError:
        raise PersistenceException('PartitionKeyGenerators - Cannot retrieve device id from request envelope!')


def applicationId(request_envelope):
    try:
        application_id = request_envelope.context.system.application.application_id
        return application_id
    except AttributeError:
        raise PersistenceException('PartitionKeyGenerators - Cannot retrieve application id from request envelope!')
