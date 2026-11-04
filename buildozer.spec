[app]
title = Chatbots
package.name = waifuchat
package.domain = com.aleja.waifuchat
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,json
version = 0.1
requirements = python3,kivy,requests
android.permissions = INTERNET,WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE
android.api = 35
android.minapi = 21
android.ndk = 25b
android.architectures = armeabi-v7a
android.accept_sdk_license = True
# Use develop branch of python-for-android: fixes pip 26 incompatibility
# (ImportError: cannot import name 'capture_logging') #3364
p4a.branch = develop

[buildozer]
log_level = 2
warn_on_root = 0
# Increase per-command timeout: full Android builds exceed 60s default
max_log_count = 1000
