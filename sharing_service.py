"""
Social Media Sharing Service for Vehicle Detection App
Handles generating social media share links
"""
from urllib.parse import quote


class SharingService:
    """Service for social media sharing"""
    
    @staticmethod
    def generate_twitter_share(text, url=None):
        """
        Generate Twitter share link
        
        Args:
            text: Text to share
            url: URL to share (optional)
        
        Returns:
            Twitter share URL
        """
        if url:
            text = f"{text} {url}"
        return f"https://twitter.com/intent/tweet?text={quote(text)}"
    
    @staticmethod
    def generate_facebook_share(url):
        """
        Generate Facebook share link
        
        Args:
            url: URL to share
        
        Returns:
            Facebook share URL
        """
        return f"https://www.facebook.com/sharer/sharer.php?u={quote(url)}"
    
    @staticmethod
    def generate_linkedin_share(url, title=None, summary=None):
        """
        Generate LinkedIn share link
        
        Args:
            url: URL to share
            title: Title (optional)
            summary: Summary (optional)
        
        Returns:
            LinkedIn share URL
        """
        share_url = f"https://www.linkedin.com/sharing/share-offsite/?url={quote(url)}"
        if title:
            share_url += f"&title={quote(title)}"
        if summary:
            share_url += f"&summary={quote(summary)}"
        return share_url
    
    @staticmethod
    def generate_whatsapp_share(text, url=None):
        """
        Generate WhatsApp share link
        
        Args:
            text: Text to share
            url: URL to share (optional)
        
        Returns:
            WhatsApp share URL
        """
        if url:
            text = f"{text} {url}"
        return f"https://api.whatsapp.com/send?text={quote(text)}"
    
    @staticmethod
    def generate_email_share(subject, body, url=None):
        """
        Generate email share link
        
        Args:
            subject: Email subject
            body: Email body
            url: URL to include (optional)
        
        Returns:
            Email share URL
        """
        if url:
            body = f"{body}\n\n{url}"
        return f"mailto:?subject={quote(subject)}&body={quote(body)}"
    
    @staticmethod
    def generate_share_links(title, description, url, vehicle_count=0):
        """
        Generate all social media share links
        
        Args:
            title: Title for sharing
            description: Description for sharing
            url: URL to share
            vehicle_count: Number of vehicles detected (optional)
        
        Returns:
            Dictionary with all share links
        """
        # Generate share text
        share_text = f"{title}\n{description}"
        if vehicle_count > 0:
            share_text = f"🚗 Detected {vehicle_count} vehicles!\n{share_text}"
        
        return {
            'twitter': SharingService.generate_twitter_share(share_text, url),
            'facebook': SharingService.generate_facebook_share(url),
            'linkedin': SharingService.generate_linkedin_share(url, title, description),
            'whatsapp': SharingService.generate_whatsapp_share(share_text, url),
            'email': SharingService.generate_email_share(title, share_text, url)
        }
