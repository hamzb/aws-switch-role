# aws-switch-role

# Description
aws-swtich-role is a Python utility that makes is easy for you to assume AWS roles in different AWS accounts. It allows you to setup and manage a config file containing your AWS accounts information, and then switch to those accounts as you please. This utility uses AWS STS API.

## Installation
In Progress
## Usage
usage: aws-switch-role.py [-h]
                          {set-default,list-account,set-account,remove-account,assume-role}
                          ...

optional arguments:
  -h, --help            show this help message and exit

sub-commands:
  actions to execute

  {set-default,list-account,set-account,remove-account,assume-role}
    set-default         sets default configuration  
    list-account        lists the AWS accounts  
    set-account         Adds or modifys the settings of an AWS account  
    remove-account      removes an AWS account from configuration  
    assume-role         assumes the AWS role of the specified AWS account  

To use aws-switch-role utility, you should start by setting a configuration file. The location of this file is $HOME/.aws-switch-role/config. It contains a main section for the default settings, and a section for each AWS account you want to define. 

The settings you can configure for the main section are the followings:
- use_mfa [yes/no]: Does the account to which you are switching require mfa?
- iam_role: the default IAM role to assume
- mfa_device: the default MFA device to use
- default_profile: The default AWS profile to use when switching to an AWS account

The settings you can configure for an account section are the followings:
- account_id: The AWS account ID
- use_mfa [yes/no]: Does the account to which you are switching require mfa?
- iam_role: the IAM role to assume
- mfa_device: the MFA device to use
- default_profile: The AWS profile to use when switching to an AWS account

If the same setting is defined in both the main section and an account section, the account section value overrides the main section value.

Configuration file sample:

[main]  
use_mfa = yes  
iam_role = AdminRole  
mfa_device = arn:aws:iam::xxxxxxxxxx:mfa/john.doe  
default_profile = default  
  
[account_A]  
account_id = 0123456789  
  
[account_B]  
account_id = 987654321  
iam_role = ConsultantRole  
use_mfa = no  

To switch to an AWS account, run the utility as follow: aws-switch-role.py assume-role --account account_name. The utility will return a json containing:
- AWS Access Key ID
- AWS Secret Access key
- AWS STS Token
- Account Name
