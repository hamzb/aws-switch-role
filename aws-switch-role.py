#!/usr/bin/env python

from utils import *
import sys
import argparse
import ConfigParser
import os
import boto3

config_dir = os.path.expanduser("~") + '/.aws-switch-role'
config_file = config_dir + '/config'
logger = set_logger()


def check_file(file_name):
	response = os.path.isfile(file_name)
	return response

def set_option(parser, section, option, value):
	if not value:
		if parser.has_option(section, option):
			parser.remove_option(section, option)
	else:
		parser.set(section, option, value)

def setDefault(args):
	response = check_file(config_file)
	if not response:
		print "Configuration file not found. Creating " + config_file
		if not os.path.isdir(config_dir):
			os.makedirs(config_dir)
		open(config_file,'w')
	parser = ConfigParser.SafeConfigParser()
	parser.read(config_file)
	if not parser.has_section('main'):
		parser.add_section('main')
	mfa_device = raw_input('Enter your default MFA device ID: ')
	iam_role = raw_input('Enter the default IAM role name you will be assuming: ')
	use_mfa = raw_input('Is MFA required by default? [yes/no]: ')
	set_option(parser, 'main', 'mfa_device', mfa_device)
	set_option(parser, 'main', 'iam_role', iam_role)
	set_option(parser, 'main', 'use_mfa', use_mfa)
	with open(config_file, 'w') as file:
		parser.write(file)


def listAccounts(args):
	response = check_file(config_file)
	if not response:
		raise ValueError('Couldnt find config file ' + config_file + '. Make sure to run aws-switch-role set-default to generate it and set the default parameters')

def setAccount(args):
	response = check_file(config_file)
	if not response:
		print 'Couldnt find config file ' + config_file + '. Make sure to run aws-switch-role set-default to generate it and set the default parameters'
		exit(1)
	parser = ConfigParser.SafeConfigParser()
	parser.read(config_file)
	account = raw_input('Enter the account name: ')
	if not account:
		raise ValueError('Account name is invalid')
	if not parser.has_section(account):
		parser.add_section(account)
	account_id = raw_input('Enter the account ID: ')
	if not account_id:
		raise ValueError('Account ID is invalid')
	set_option(parser, account, 'account_id', account_id)
	iam_role = raw_input('Enter the IAM role: ')
	set_option(parser, account, 'iam_role', iam_role)
	mfa_device = raw_input('Enter the mfa device: ')
	set_option(parser, account, 'mfa_device', mfa_device)
	use_mfa = raw_input('Does this account require mfa? [yes/no] ')
	set_option(parser, account, 'use_mfa', use_mfa)
	with open(config_file, 'wb') as file:
		parser.write(file)


def removeAccount(args):
	response = check_file(config_file)
	if not response:
		raise ValueError('Couldnt find config file ' + config_file + '. Make sure to run aws-switch-role set-default to generate it and set the default parameters')
		
	parser = ConfigParser.SafeConfigParser()
	parser.read(config_file)
	account = raw_input('Enter the account name: ')
	if not account:
		raise ValueError('Account name is invalid')
	if parser.has_section(account):
		parser.remove_section(account)
	else:
		print 'Account ' + account + ' does not exist'
	with open(config_file, 'wb') as file:
		parser.write(file)

def assumeRole(args):
	response = check_file(config_file)
	if not response:
		raise ValueError('Couldnt find config file ' + config_file + '. Make sure to run aws-switch-role set-default to generate it and set the default parameters')
	parser = ConfigParser.SafeConfigParser()
	parser.read(config_file)
	if parser.has_option('main', 'iam_role'):
		iam_role = parser.get('main', 'iam_role')
	if parser.has_option('main', 'mfa_device'):
		mfa_device = parser.get('main', 'mfa_device')
	if parser.has_option('main', 'use_mfa'):
		use_mfa = ('main', 'use_mfa')
	account = args.acc
	if not parser.has_section(account):
		raise ValueError('Account is invalid')
	if parser.has_option(account, 'iam_role'):
		iam_role = parser.get(account, 'iam_role')
	if parser.has_option(account, 'mfa_device'):
		mfa_device = parser.get(account, 'mfa_device')
	if parser.has_option(account, 'use_mfa'):
		use_mfa = (account, 'use_mfa')
	if parser.has_option(account, 'account_id'):
		account_id = parser.get(account, 'account_id')
	role = 'arn:aws:iam::' + account_id + ':role/' + iam_role
	session = account
	client = boto3.client('sts')
	mfa_code = raw_input('Enter your MFA code: ')
	try:
		response = client.assume_role(RoleArn=role, RoleSessionName=session, SerialNumber=mfa_device, TokenCode=mfa_code)
		print 'Access Key Id: ' + response['Credentials']['AccessKeyId']
		print 'Secret Access Key: ' + response['Credentials']['SecretAccessKey']
		print 'Session Token: '  + response['Credentials']['SessionToken']

	except Exception as err:
		raise ValueError(format(err))


def showStatus(args):
	print 'creds status'

		

parser = argparse.ArgumentParser()
subparsers = parser.add_subparsers(title='sub-commands', description='actions to execute')

parser_set_default = subparsers.add_parser('set-default', help='sets default configuration')
parser_set_default.set_defaults(func=setDefault)

paser_list_accounts = subparsers.add_parser('list-accounts', help='lists the AWS accounts')
paser_list_accounts.set_defaults(func=listAccounts)

parser_set_account = subparsers.add_parser('set-account', help='Adds or modifys the settings of an AWS account')
parser_set_account.set_defaults(func=setAccount)

parser_remove_account = subparsers.add_parser('remove-account', help='removes an AWS account from configuration')
parser_remove_account.set_defaults(func=removeAccount)

parser_assume_role = subparsers.add_parser('assume-role', help='assumes the AWS role of the specified AWS account')
parser_assume_role.set_defaults(func=assumeRole)
exGroup = parser_assume_role.add_mutually_exclusive_group()
exGroup.add_argument('--account-id', dest='acc_id', help='Account ID of the AWS account you want to access')
exGroup.add_argument('--account', dest='acc', help='Alias of the AWS Account you want to access')

parser_status = subparsers.add_parser('status', help='shows the status of AWS credentials')
parser_status.set_defaults(func=showStatus)

args = parser.parse_args()
try:
	args.func(args)
except Exception as err:
	print str(err)

