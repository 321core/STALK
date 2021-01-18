import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SECRET_KEY = '88wz8#dntgs9op%ufpf0vnrank6d&p7w^0j@_()!xr%es_x(#4'
DEBUG = True

ALLOWED_HOSTS = []

# Application definition

INSTALLED_APPS = (
    'suit',

    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    'api',
)

MIDDLEWARE = (
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
)

ROOT_URLCONF = 'stalk_index_server.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'stalk_index_server.wsgi.application'

# Database
# https://docs.djangoproject.com/en/1.8/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'HOST': '',
        'NAME': 'STALK',
        'USER': 'stalk',
        'PASSWORD': 'stalk'
    }
}

# Internationalization
# https://docs.djangoproject.com/en/1.8/topics/i18n/
LANGUAGE_CODE = 'ko-KR'
TIME_ZONE = 'Asia/Seoul'
USE_I18N = True
USE_L10N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.8/howto/static-files/

STATIC_URL = '/static/'
STATIC_ROOT = '/usr/share/nginx/stalk.321core.com/static/'

#
CACHEOPS_REDIS = "redis://localhost:6379/3"
CACHEOPS_DEFAULTS = {
    'timeout': 60 * 60 * 24
}
CACHEOPS = {
    '*.*': {
        'ops': 'all',
        'cache_on_save': True,
        'timeout': 60 * 60 * 24
    }
}
CACHEOPS_DEGRADE_ON_FAILURE = False

SUIT_CONFIG = {
    # header
    'ADMIN_NAME': u'S-TALK',
    # 'HEADER_DATE_FORMAT': 'l, j. F Y',
    # 'HEADER_TIME_FORMAT': 'H:i',

    # forms
    # 'SHOW_REQUIRED_ASTERISK': True,  # Default True
    # 'CONFIRM_UNSAVED_CHANGES': True, # Default True

    # menu
    # 'SEARCH_URL': '/admin/auth/user/',
    # 'MENU_ICONS': {
    #    'sites': 'icon-leaf',
    #    'auth': 'icon-lock',
    # },
    # 'MENU_OPEN_FIRST_CHILD': True, # Default True
    # 'MENU_EXCLUDE': ('auth.group',),
    # 'MENU': (
    #     # 'sites',
    #     {
    #         'label': u'계정 시스템',
    #         'models': ('account.User',)
    #     },
    #     {
    #         'label': u'센서 시스템',
    #         'models': (
    #             'sensor.Site',
    #             'sensor.Region',
    #             'sensor.Area',
    #             'sensor.Zone',
    #             'sensor.Gate',
    #             'sensor.Company',
    #             'sensor.Department',
    #             'sensor.Person',
    #             'sensor.Individual',
    #             'sensor.Mobile',
    #             'sensor.Ref',
    #             'sensor.SensorType',
    #             'sensor.SensorFixed',
    #             'sensor.SensorMoving',
    #             'sensor.SensorWearable',
    #             'sensor.LocationUpdate',
    #             'sensor.LocationHistory',
    #             'sensor.MobileStatusUpdate',
    #             'sensor.MobileStatusHistory',
    #             'sensor.RefStatusUpdate',
    #             'sensor.RefStatusHistory',
    #             'sensor.SensorDataFixedUpdate',
    #             'sensor.SensorDataFixedHistory',
    #             'sensor.SensorDataMovingUpdate',
    #             'sensor.SensorDataMovingHistory',
    #             'sensor.SensorDataWearableUpdate',
    #             'sensor.SensorDataWearableHistory',
    #             'sensor.LocStatUpdate',
    #             'sensor.LocStatHistory',
    #             'sensor.ErrCode',
    #             'sensor.Edge',
    #             'sensor.EdgeType',
    #         )
    #     },
    # ),

    # misc
    # 'LIST_PER_PAGE': 15
}
