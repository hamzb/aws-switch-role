import boto3
import logging

def set_logger():
	logger = logging.getLogger(__name__)
	logger.setLevel(logging.INFO)
	handler = logging.StreamHandler()
	handler.setLevel(logging.INFO)
	formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', "%Y-%m-%d %H:%M:%S")
	handler.setFormatter(formatter)
	logger.addHandler(handler)
	return logger

def assume_iam_role(iam_role,session,mfa_id,mfa_code):
	client = boto3.client('sts')
	try:
		response = client.assume_role(RoleArn=iam_role, RoleSessionName=session, SerialNumber=mfa_id, TokenCode=mfa_code)
		return response
	except Exception as err:
		raise ValueError(format(err))

		

