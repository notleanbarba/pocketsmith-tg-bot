# Pocketsmith Telegram bot

Pocketsmith Telegram bot helps you to manage your pockesmith account from a Telegram chat. Currently, you can use it to upload transactions to your Pocketsmith account. See more about [commands](/README.md#available-commands).

## 1. Installation - Part 1

Installation is not extremely easy but it was simplified good enough for a person with minimal knowledge in AWS, Linux and DNS.

Before you can install the bot, you will need the following ingredients:

1. A Pocketsmith account
2. A domain
3. A Telegram bot
4. An AWS account (or your preffered cloud provider. This guide is based on AWS)

### 1.1. Preparing your Pocketsmith account

Once you have your Pocketsmith account setup, you can get the API key you need for your bot. An API key is a secret password your bot is going to use to verify itself as your bot.

To get your Pocketsmith key follow the next steps:

1. Login to your account
2. Go to your **profile**
3. Hit on **Security & integrations**
4. Click on **Manage developer keys**
5. Create a new key and save it securely. _Remember_: everyone with this key can use it to login to your Pocketsmith account

### 1.2. Getting a domain

Your bot will need a domain to work properly. A domain is paid and you can get a cheap one from [Namecheap](https://namecheap.com/)

### 1.3. Creating your Telegram bot

A Telegram bot is a special Telegram user with which you are able to chat. This user is an interface between you and the code is running in your web server. Creating one is really easy, follow the next steps:

1. Open your Telegram app and start a chat with @BotFather (BotFather is a bot used to create and manage other bots.)
2. Send "/newbot" to @BotFather
3. Follow the promps. This will give you an API key. As with the Pocketsmith key, save it securely. This is really import as it can be used to control your bot
4. Send "/setinline" to @BotFather and select your newly created bot. This will enable Inline Mode for your bot
5. Send "/setjoingroups" to @BotFather and select your bot, then disable the join group permission. This will give more privacy to your bot as it will not be able to join groups

### 1.4. Register your AWS account

If you have an AWS account you can skip this step. If not, go to [Amazon Web Services](https://portal.aws.amazon.com/billing/signup) and create a new account.

This guide use AWS as a cloud provider. However, if you like to use another cloud service you are more than welcome to do it.

## 2. Installation - Part 2

Once all [Installation - Part 1](/README.md#1-installation---part-1), you can start deploying your bot.

First, login to your AWS account and go to Lightsail service. Here you are going to create an instance, a DNS Zone and a static IP.

### 2.1. Creating an instance

The Lightsail instance is going to be the brain of your bot deployment. Create a new instance with the following steps:

1. Hit **Instances** on your Lightsail dashboard
2. Click **Create instance**
3. Under **Select a platform**, choose Select _Linux/Unix_ and under **Select a blueprint**, choose _Operating System (OS) only_ with _Amazon Linux 2023_ as **OS**
4. _Optional_: Rename your instance with the name you prefer
5. Enter your instance, go to the **Networking** tab and click on **Add rule**. Under **Application**, select _HTTPS_. Check the **Restrict to IP address** box and add the this two addresses _149.154.160.0/20_ and _91.108.4.0/22_
6. _Optional_: You can disable IPv6 as it is not going to useful at all.

Done! In a few seconds, your new instance is about to be up and running. Also, it will only accept secure connections from Telegram and nobody else. We can proceed to network now.

### 2.2. Creating a DNS zone

A DNS zone is the configuration of your domain name. It will resolve what to do when you enter your domain in the web browser or where to redirect a request made in Telegram for your bot. Keep in mind that this guide works if you registered your domain in Namecheap, if you made it on Amazon Route 53 it's even easier!

1. Go to **Domains & DNS** on your Lightsail dashboard
2. Click **Create DNS zone**
3. Under **Domain source**, hit _Use a domain from another registrar_ then enter your domain in the box below
4. Click **Create DNS zone**. This will give you a bunch of nameservers, these are addresses that will give AWS power to control your domain. Copy all of them.
5. Now, go to your namecheap dashboard and look for the **Domain**/**Nameservers** section in your domain management and select _Custom DNS_. Then add all of the previous copied nameservers from Lightsail.

Good! Now you have authorized AWS to use your domain. Next we are going to set a subdomain like _bot.yourdomain.com_ for your bot.

### 2.3. Creating a static IP

An static IP is a never changing address that will be assigned to your bot. This will allow your bot to be called using a subdomain like _bot.yourdomain.com_.

1. Go to **Networking** on your Lightsail dashboard
2. Click on **Create static IP**
3. Under **Attach to an instance**, choose your instance created in [2.1. Creating an instance](/README.md#21-creating-an-instance)
4. _Optional_: Name your new IP as you want
5. Hit **Create**
6. Click on **Domains** and **Assign domain**. Select your domain and under **Select a domain**, choose _A subdomain of $yourdomain_. Then enter _bot_ or whatever you want
7. Click on **Assign**

Now, whenever you call your subdomain you are going to be redirected to your bot server.

### 2.4. Starting your bot

Uff, that was long. Now, if everything went OK, you are ready to start your bot.

1. Connect to your instance: The easiest way is to use the browser. Go to your instance and in **Connect** tab click **Connect using SSH**. This will prompt out a SSH terminal.
2. Once connected, enter this command:

```bash
sudo su
```

3. Nice, you are logged as root. Fill up, copy and paste the following codeblock. This will give the starting script all the information it needs to execute.

```bash
export DOMAIN=Enter.your.custom.subdomain.here (Like bot.google.com)
export EMAIL=Enter your emai address
export POCKETSMITH_TOKEN=Enter your Pocketsmith API key
export TELEGRAM_TOKEN=Enter your Telegram API key
export TG_USER=Enter your Telegram user id
curl -L https://raw.githubusercontent.com/notleanbarba/pocketsmith-tg-bot/master/scripts/install | bash
```

You finished! If everything went good, you should have your Pocketsmith Telegram bot up and running.

## Available commands
