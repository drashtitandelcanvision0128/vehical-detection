"""
Translation System for Vehicle Detection App
Supports English and Hindi languages
"""

TRANSLATIONS = {
    'en': {
        # Navigation
        'home': 'Home',
        'dashboard': 'Dashboard',
        'history': 'History',
        'live_detection': 'Live Detection',
        'logout': 'Logout',
        'login': 'Login',
        'register': 'Register',
        
        # Auth
        'username': 'Username',
        'password': 'Password',
        'confirm_password': 'Confirm Password',
        'email': 'Email',
        'login_success': 'Login successful!',
        'login_failed': 'Invalid username or password.',
        'register_success': 'Registration successful! Please login.',
        'register_failed': 'Registration failed. Please try again.',
        'password_mismatch': 'Passwords do not match.',
        'password_short': 'Password must be at least 6 characters.',
        'all_fields_required': 'All fields are required.',
        'user_exists': 'Username or email already exists.',
        
        # Dashboard
        'analytics_dashboard': 'Analytics Dashboard',
        'overview': 'Overview of detection statistics and trends',
        'total_detections': 'Total Detections',
        'vehicles_detected': 'Vehicles Detected',
        'processing_time': 'Processing Time',
        'avg_vehicles': 'Avg Vehicles',
        'detection_by_type': 'Detection by Type',
        'vehicle_breakdown': 'Vehicle Breakdown',
        'daily_trends': 'Daily Trends',
        'hourly_distribution': 'Hourly Distribution',
        'top_users': 'Top Users by Activity',
        'performance_metrics': 'Performance Metrics',
        
        # Detection
        'upload_image': 'Upload Image',
        'upload_video': 'Upload Video',
        'start_detection': 'Start Detection',
        'detecting': 'Detecting...',
        'detection_complete': 'Detection Complete',
        'vehicles_found': 'Vehicles Found',
        'confidence': 'Confidence',
        'no_vehicles': 'No vehicles detected',
        
        # History
        'past_detections': 'Past Detections',
        'view_history': 'View detection history',
        'download_report': 'Download Report',
        'view_report': 'View Report',
        'view_video': 'View Video',
        'delete': 'Delete',
        'no_history': 'No Detection History',
        'no_history_desc': 'Upload images or videos to see your detection history here',
        
        # Common
        'loading': 'Loading...',
        'error': 'Error',
        'success': 'Success',
        'warning': 'Warning',
        'info': 'Information',
        'cancel': 'Cancel',
        'save': 'Save',
        'delete_confirm': 'Are you sure you want to delete this?',
        'back': 'Back',
        'next': 'Next',
        'previous': 'Previous',
        'search': 'Search',
        'filter': 'Filter',
        'export': 'Export',
        'import': 'Import',
        
        # Vehicle Types
        'car': 'Car',
        'motorcycle': 'Motorcycle',
        'bus': 'Bus',
        'truck': 'Truck',
        
        # Messages
        'welcome': 'Welcome',
        'please_login': 'Please login to access this page.',
        'logged_out': 'You have been logged out.',
    },
    'hi': {
        # Navigation
        'home': 'होम',
        'dashboard': 'डैशबोर्ड',
        'history': 'इतिहास',
        'live_detection': 'लाइव डिटेक्शन',
        'logout': 'लॉगआउट',
        'login': 'लॉगिन',
        'register': 'रजिस्टर',
        
        # Auth
        'username': 'यूजरनेम',
        'password': 'पासवर्ड',
        'confirm_password': 'पासवर्ड की पुष्टि करें',
        'email': 'ईमेल',
        'login_success': 'लॉगिन सफल!',
        'login_failed': 'अमान्य यूजरनेम या पासवर्ड।',
        'register_success': 'रजिस्ट्रेशन सफल! कृपया लॉगिन करें।',
        'register_failed': 'रजिस्ट्रेशन विफल। कृपया पुनः प्रयास करें।',
        'password_mismatch': 'पासवर्ड मेल नहीं खाते।',
        'password_short': 'पासवर्ड कम से कम 6 अक्षर का होना चाहिए।',
        'all_fields_required': 'सभी फ़ील्ड आवश्यक हैं।',
        'user_exists': 'यूजरनेम या ईमेल पहले से मौजूद है।',
        
        # Dashboard
        'analytics_dashboard': 'विश्लेषण डैशबोर्ड',
        'overview': 'डिटेक्शन आँकड़ों और रुझानों का अवलोकन',
        'total_detections': 'कुल डिटेक्शन',
        'vehicles_detected': 'वाहन पता चले',
        'processing_time': 'प्रोसेसिंग समय',
        'avg_vehicles': 'औसत वाहन',
        'detection_by_type': 'प्रकार के अनुसार डिटेक्शन',
        'vehicle_breakdown': 'वाहन विवरण',
        'daily_trends': 'दैनिक रुझान',
        'hourly_distribution': 'घंटावार वितरण',
        'top_users': 'शीर्ष उपयोगकर्ता',
        'performance_metrics': 'प्रदर्शन मेट्रिक्स',
        
        # Detection
        'upload_image': 'छवि अपलोड करें',
        'upload_video': 'वीडियो अपलोड करें',
        'start_detection': 'डिटेक्शन शुरू करें',
        'detecting': 'डिटेक्शन हो रहा है...',
        'detection_complete': 'डिटेक्शन पूर्ण',
        'vehicles_found': 'वाहन मिले',
        'confidence': 'विश्वास',
        'no_vehicles': 'कोई वाहन नहीं मिला',
        
        # History
        'past_detections': 'पिछले डिटेक्शन',
        'view_history': 'डिटेक्शन इतिहास देखें',
        'download_report': 'रिपोर्ट डाउनलोड करें',
        'view_report': 'रिपोर्ट देखें',
        'view_video': 'वीडियो देखें',
        'delete': 'हटाएं',
        'no_history': 'कोई डिटेक्शन इतिहास नहीं',
        'no_history_desc': 'डिटेक्शन इतिहास देखने के लिए छवियां या वीडियो अपलोड करें',
        
        # Common
        'loading': 'लोड हो रहा है...',
        'error': 'त्रुटि',
        'success': 'सफलता',
        'warning': 'चेतावनी',
        'info': 'जानकारी',
        'cancel': 'रद्द करें',
        'save': 'सहेजें',
        'delete_confirm': 'क्या आप वाकई इसे हटाना चाहते हैं?',
        'back': 'वापस',
        'next': 'अगला',
        'previous': 'पिछला',
        'search': 'खोजें',
        'filter': 'फ़िल्टर',
        'export': 'निर्यात',
        'import': 'आयात',
        
        # Vehicle Types
        'car': 'कार',
        'motorcycle': 'मोटरसाइकिल',
        'bus': 'बस',
        'truck': 'ट्रक',
        
        # Messages
        'welcome': 'स्वागत',
        'please_login': 'इस पेज तक पहुंचने के लिए कृपया लॉगिन करें।',
        'logged_out': 'आप लॉग आउट हो गए हैं।',
    }
}


def get_translation(key, lang='en'):
    """
    Get translation for a key
    
    Args:
        key: Translation key
        lang: Language code ('en' or 'hi')
    
    Returns:
        Translated string or key if not found
    """
    if lang not in TRANSLATIONS:
        lang = 'en'
    
    return TRANSLATIONS[lang].get(key, key)


def set_language(lang='en'):
    """
    Validate and return language code
    
    Args:
        lang: Language code
    
    Returns:
        Valid language code ('en' or 'hi')
    """
    if lang not in TRANSLATIONS:
        return 'en'
    return lang
