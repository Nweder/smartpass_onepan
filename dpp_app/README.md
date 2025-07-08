# Denoiser for Scattering Images

This web app provides an interface for creating a Machine Learning Model for reducing the noise in a Scattering Image. This README file contains what is necessary to know for running the web app.

## Table of content
- [Download or clone repository](#download-or-clone-repository)
- [Setting environment](#setting-environment)
- [Running web app](#running-web-app)

## Download or clone repository
To run the code is necessary to have it locally. You can go in two ways:
- Download, if you don't need to do any modification.
 
- Otherwise, clone repository, you can follow this [tutorial](https://docs.gitlab.com/ee/topics/git/clone.html) is you need support.
 
## Setting Environment
This procedure is for creating an enviroment and installing the proper libraries. You only need to do this once.
1. Install Anaconda using the following link
[https://www.anaconda.com/]
It is important to click at add path to environment variables while installing
       
2. Open a terminal, and go to the folder `/UI_denoiser`
3. Run `/batch_scripts/0_EnvironmentSetUp.bat`

## Running web app
This procedure is for running the web app. 
1. Open a terminal, and go to the folder `/UI_denoiser`
2. Run `/batch_scripts/1_RunWebInterface.bat`. If the navigator is not open automatically, just click on Local URL or Network URL. 

In the web app you will find 3 procedures: 1)Create ground truth, 2)Train and, 3)Predict. A brief explanation of each procedure is presented in the web app.