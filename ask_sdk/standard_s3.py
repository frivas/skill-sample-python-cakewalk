# -*- coding: utf-8 -*-

import typing

from ask_sdk_core.skill_builder import SkillBuilder
from ask_sdk_core.api_client import DefaultApiClient
from ask_sdk_s3_persistence.S3PersistenceAdapter import S3PersistenceAdapter

if typing.TYPE_CHECKING:
    from typing import Callable
    from ask_sdk_model import RequestEnvelope
    from ask_sdk_core.skill_builder import SkillConfiguration
    from boto3.resources.base import ServiceResource


class StandardSkillBuilder(SkillBuilder):
    def __init__(
            self, bucket_name=None, s3_client=None,
            object_generator=None, path_prefix=None, api_client=None):
        """
        Skill Builder with api client and db adapter coupling to Skill.
        """
        super(StandardSkillBuilder, self).__init__()
        self.bucket_name = bucket_name
        self.s3_client = s3_client
        self.object_generator = object_generator
        self.path_prefix = path_prefix if path_prefix else ''
        self.api_client = api_client

    @property
    def skill_configuration(self):
        # type: () -> SkillConfiguration
        """Create the skill configuration object using the registered
        components.
        """
        skill_config = super(StandardSkillBuilder, self).skill_configuration
        skill_config.api_client = DefaultApiClient()

        if self.bucket_name is not None:
            kwargs = {"bucket_name": self.bucket_name}

            if self.s3_client:
                kwargs["s3_client"] = self.s3_client

            if self.object_generator:
                kwargs["object_generator"] = self.object_generator

            if self.path_prefix:
                kwargs["path_prefix"] = self.path_prefix

            skill_config.persistence_adapter = S3PersistenceAdapter(**kwargs)
        return skill_config
