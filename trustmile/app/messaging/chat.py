__author__ = 'james'


from app.ops.consumer_operations import log_operation
from app.ops.base import BaseOperation, log_operation
from app.model.meta.base import commit_on_success


class MessageSender(BaseOperation):

    @log_operation
    @commit_on_success
    def perform(self, value, **kwargs):
        pass