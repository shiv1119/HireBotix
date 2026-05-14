# utils/github_service.py
import requests
from datetime import datetime, timedelta
import logging
from collections import defaultdict
from django.core.cache import cache
from django.utils import timezone
import re

logger = logging.getLogger(__name__)


class GitHubService:
    """GitHub service to fetch user stats - no token required"""
    
    @staticmethod
    def clean_github_url(url):
        """
        Clean and normalize GitHub URLs
        Handles cases like:
        - https://github.com/github.com/shiv1119 -> https://github.com/shiv1119
        - github.com/shiv1119 -> https://github.com/shiv1119
        - https://github.com/shiv1119 -> https://github.com/shiv1119
        - shiv1119 -> https://github.com/shiv1119
        """
        if not url:
            return None
        
        # Strip whitespace
        url = url.strip()
        
        # Remove any protocol prefix temporarily for processing
        has_protocol = url.startswith(('http://', 'https://'))
        if has_protocol:
            # Extract the URL without protocol for processing
            protocol_match = re.match(r'^(https?://)', url)
            protocol = protocol_match.group(1) if protocol_match else 'https://'
            url_without_protocol = url[len(protocol):]
        else:
            protocol = 'https://'
            url_without_protocol = url
        
        # Remove duplicate github.com pattern
        # Pattern: github.com/github.com/username -> github.com/username
        url_without_protocol = re.sub(
            r'^github\.com/github\.com/', 
            'github.com/', 
            url_without_protocol
        )
        
        # Also handle the case with www
        url_without_protocol = re.sub(
            r'^www\.github\.com/github\.com/', 
            'github.com/', 
            url_without_protocol
        )
        
        # Remove any duplicate patterns like github.com/github.com/github.com/username
        while 'github.com/github.com/' in url_without_protocol:
            url_without_protocol = re.sub(
                r'github\.com/github\.com/', 
                'github.com/', 
                url_without_protocol
            )
        
        # Ensure it starts with github.com (if it's a GitHub URL)
        if not url_without_protocol.startswith('github.com/') and not url_without_protocol.startswith('www.github.com/'):
            # Check if it's just a username
            if '/' not in url_without_protocol and '.' not in url_without_protocol:
                # Assume it's a username
                url_without_protocol = f"github.com/{url_without_protocol}"
            elif 'github.com' in url_without_protocol:
                # Extract username from malformed URL
                match = re.search(r'github\.com/([^/?#]+)', url_without_protocol)
                if match:
                    username = match.group(1)
                    url_without_protocol = f"github.com/{username}"
        
        # Build final URL
        clean_url = f"{protocol}{url_without_protocol}"
        
        # Remove trailing slashes
        clean_url = clean_url.rstrip('/')
        
        # Validate the URL format
        github_pattern = r'^https?://(www\.)?github\.com/[a-zA-Z0-9_-]+/?$'
        if re.match(github_pattern, clean_url):
            return clean_url
        else:
            # If still invalid, try one more extraction
            match = re.search(r'github\.com/([a-zA-Z0-9_-]+)', url)
            if match:
                return f"https://github.com/{match.group(1)}"
        
        return None
    
    @staticmethod
    def extract_username(github_url):
        """Extract username from GitHub URL"""
        if not github_url:
            return None
        
        # First clean the URL
        clean_url = GitHubService.clean_github_url(github_url)
        if not clean_url:
            return None
        
        patterns = [
            r'github\.com/([^/?#]+)',
            r'https?://github\.com/([^/?#]+)',
            r'^([a-zA-Z0-9_-]+)$',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, clean_url)
            if match:
                return match.group(1)
        return None
    
    @staticmethod
    def fetch_user_stats(username):
        """
        Fetch GitHub user stats using public API
        Returns dict with essential stats only
        """
        # Check cache first (30 minute cache for API responses)
        cache_key = f"github_api_{username}"
        cached_response = cache.get(cache_key)
        if cached_response:
            logger.info(f"Returning cached GitHub API response for {username}")
            return cached_response
        
        try:
            # Fetch user repos
            repos_url = f"https://api.github.com/users/{username}/repos"
            params = {'per_page': 100, 'sort': 'updated', 'type': 'all'}
            repos_response = requests.get(repos_url, params=params, timeout=10)
            
            if repos_response.status_code == 404:
                return {'error': 'User not found', 'success': False}
            if repos_response.status_code != 200:
                return {'error': f'GitHub API error: {repos_response.status_code}', 'success': False}
            
            repos_data = repos_response.json()
            
            # Calculate language stats by bytes
            languages_bytes = defaultdict(int)
            total_stars = 0
            total_forks = 0
            total_commits = 0
            
            for repo in repos_data:
                # Stars and forks
                total_stars += repo.get('stargazers_count', 0)
                total_forks += repo.get('forks_count', 0)
                
                # Get commit count for the repository
                repo_commits = 0
                try:
                    # Method 1: Try to get contributor stats (more accurate but rate limited)
                    contributor_url = f"https://api.github.com/repos/{username}/{repo['name']}/contributors"
                    contributor_response = requests.get(contributor_url, timeout=10)
                    
                    if contributor_response.status_code == 200:
                        contributors = contributor_response.json()
                        # Find the current user's contributions
                        for contributor in contributors:
                            if contributor.get('login') == username:
                                repo_commits = contributor.get('contributions', 0)
                                break
                    
                    # Method 2: If contributor stats not available or empty, try commits endpoint
                    if repo_commits == 0:
                        commits_url = f"https://api.github.com/repos/{username}/{repo['name']}/commits"
                        commits_params = {'author': username, 'per_page': 1}
                        commits_response = requests.get(commits_url, params=commits_params, timeout=10)
                        
                        if commits_response.status_code == 200:
                            # Check link header for total count
                            link_header = commits_response.headers.get('Link', '')
                            if 'rel="last"' in link_header:
                                # Parse total pages from link header
                                import re
                                last_page_match = re.search(r'page=(\d+)>; rel="last"', link_header)
                                if last_page_match:
                                    repo_commits = int(last_page_match.group(1))
                                else:
                                    # If no last page, count returned commits
                                    repo_commits = len(commits_response.json())
                            else:
                                repo_commits = len(commits_response.json())
                    
                    total_commits += repo_commits
                    logger.debug(f"Repo {repo['name']}: {repo_commits} commits")
                    
                except Exception as e:
                    logger.warning(f"Failed to fetch commits for {repo['name']}: {str(e)}")
                    # Try alternative method: get commits via activity stats
                    try:
                        stats_url = f"https://api.github.com/repos/{username}/{repo['name']}/stats/participation"
                        stats_response = requests.get(stats_url, timeout=10)
                        if stats_response.status_code == 200:
                            stats_data = stats_response.json()
                            if 'all' in stats_data:
                                repo_commits = sum(stats_data['all'])
                                total_commits += repo_commits
                                logger.debug(f"Repo {repo['name']} via stats: {repo_commits} commits")
                    except:
                        pass
                    continue
                
                # Fetch languages for each repo (by bytes)
                lang_url = f"https://api.github.com/repos/{username}/{repo['name']}/languages"
                try:
                    lang_response = requests.get(lang_url, timeout=10)
                    if lang_response.status_code == 200:
                        langs = lang_response.json()
                        for lang, bytes_count in langs.items():
                            languages_bytes[lang] += bytes_count
                except Exception as e:
                    logger.warning(f"Failed to fetch languages for {repo['name']}: {str(e)}")
                    continue
            
            # Convert bytes to percentage
            total_bytes = sum(languages_bytes.values())
            languages = {}
            for lang, bytes_count in languages_bytes.items():
                languages[lang] = round((bytes_count / total_bytes) * 100, 2) if total_bytes > 0 else 0
            
            # Fetch user events for PRs and Issues (these work better with events API)
            events_url = f"https://api.github.com/users/{username}/events"
            events_response = requests.get(events_url, timeout=10)
            events_data = events_response.json() if events_response.status_code == 200 else []
            
            # Calculate PRs and Issues from events
            total_prs = 0
            total_issues = 0
            
            for event in events_data:
                event_type = event.get('type')
                if event_type == 'PullRequestEvent':
                    total_prs += 1
                elif event_type == 'IssuesEvent':
                    total_issues += 1
            
            # Process contributions for timeline (from events)
            contributions = []
            for event in events_data[:90]:
                try:
                    date = datetime.strptime(event['created_at'][:10], '%Y-%m-%d').date()
                    contributions.append({
                        'date': date.isoformat(),
                        'count': 1
                    })
                except:
                    pass
            
            # Group contributions by date
            grouped_contributions = defaultdict(int)
            for contrib in contributions:
                grouped_contributions[contrib['date']] += contrib['count']
            
            # Format contributions for storage
            formatted_contributions = [
                {'date': date, 'count': count} 
                for date, count in grouped_contributions.items()
            ]
            
            result = {
                'success': True,
                'username': username,
                'public_repos': len(repos_data),
                'total_stars': total_stars,
                'total_forks': total_forks,
                'total_commits': total_commits,
                'total_pull_requests': total_prs,
                'total_issues': total_issues,
                'languages': languages,
                'contributions': formatted_contributions,
                'fetched_at': datetime.now().isoformat()
            }
            
            # Cache for 30 minutes to avoid hitting rate limits
            cache.set(cache_key, result, 1800)
            
            return result
            
        except requests.RequestException as e:
            logger.error(f"Request error for {username}: {str(e)}")
            return {'error': str(e), 'success': False}
        except Exception as e:
            logger.error(f"Unexpected error for {username}: {str(e)}")
            return {'error': str(e), 'success': False}


class GitHubStatsUpdater:
    """Background thread to update GitHub stats with rate limiting"""
    
    @staticmethod
    def needs_update(user):
        """Check if user needs GitHub stats update"""
        from .models import GitHubStats
        
        # Get existing stats
        stats = GitHubStats.objects.filter(user=user).first()
        
        # No stats exist - needs update
        if not stats:
            return True
        
        # Check if last fetch was more than 2 days ago
        if stats.last_fetched:
            time_since_update = timezone.now() - stats.last_fetched
            if time_since_update > timedelta(days=2):
                logger.info(f"GitHub stats for {user.username} are {time_since_update.days} days old, updating...")
                return True
        
        # Check if fetch failed and last attempt was more than 1 hour ago
        if stats.fetch_status == 'failed' and stats.last_fetched:
            time_since_failed = timezone.now() - stats.last_fetched
            if time_since_failed > timedelta(hours=1):
                logger.info(f"Retrying failed GitHub stats fetch for {user.username}")
                return True
        
        # Also check if we have a GitHub link but no stats (edge case)
        github_link = user.links.filter(name__iexact='github').first()
        if github_link and not stats.public_repos and stats.fetch_status != 'processing':
            logger.info(f"User {user.username} has GitHub link but no stats, updating...")
            return True
        
        logger.info(f"GitHub stats for {user.username} are fresh (updated {stats.last_fetched})")
        return False
    
    @staticmethod
    def update_github_stats(user):
        """Update GitHub stats for a user"""
        from .models import GitHubStats, GitHubContribution
        from collections import defaultdict
        
        # Check if update is needed before proceeding
        if not GitHubStatsUpdater.needs_update(user):
            return False
        
        # Use a lock to prevent concurrent updates for the same user
        lock_key = f"github_update_lock_{user.id}"
        if cache.get(lock_key):
            logger.info(f"GitHub stats update already in progress for {user.username}")
            return False
        
        # Set lock for 5 minutes
        cache.set(lock_key, True, 300)
        
        try:
            # Get GitHub link
            github_link = user.links.filter(name__iexact='github').first()
            if not github_link or not github_link.url:
                logger.info(f"No GitHub link found for user {user.username}")
                # Mark stats as not needed
                GitHubStats.objects.update_or_create(
                    user=user,
                    defaults={
                        'username': user.username,
                        'github_url': '',
                        'fetch_status': 'not_applicable',
                        'last_fetched': timezone.now()
                    }
                )
                return False
            
            # Clean and update the GitHub URL if needed
            original_url = github_link.url
            cleaned_url = GitHubService.clean_github_url(original_url)
            
            # If URL was malformed and got cleaned, update it in the database
            if cleaned_url and cleaned_url != original_url:
                github_link.url = cleaned_url
                github_link.save(update_fields=['url', 'updated_at'])
                logger.info(f"Cleaned GitHub URL for {user.username}: {original_url} -> {cleaned_url}")
            
            # Extract username from cleaned URL
            username = GitHubService.extract_username(github_link.url)
            if not username:
                logger.warning(f"Could not extract GitHub username from {github_link.url}")
                return False
            
            # Fetch stats
            data = GitHubService.fetch_user_stats(username)
            
            if data.get('success'):
                # Update or create GitHub stats
                stats, created = GitHubStats.objects.update_or_create(
                    user=user,
                    defaults={
                        'username': username,
                        'github_url': github_link.url,
                        'public_repos': data.get('public_repos', 0),
                        'total_stars': data.get('total_stars', 0),
                        'total_forks': data.get('total_forks', 0),
                        'total_commits': data.get('total_commits', 0),
                        'total_pull_requests': data.get('total_pull_requests', 0),
                        'total_issues': data.get('total_issues', 0),
                        'languages': data.get('languages', {}),
                        'last_fetched': timezone.now(),
                        'fetch_status': 'success',
                        'error_message': None
                    }
                )
                
                # Save contributions
                contributions = data.get('contributions', [])
                if contributions:
                    grouped = defaultdict(int)
                    for contrib in contributions:
                        grouped[contrib['date']] += contrib['count']
                    
                    for date_str, count in grouped.items():
                        GitHubContribution.objects.update_or_create(
                            github_stats=stats,
                            date=date_str,
                            defaults={'contribution_count': count}
                        )
                    
                    # Clean up old contributions (keep last 365 days)
                    cutoff_date = timezone.now().date() - timedelta(days=365)
                    GitHubContribution.objects.filter(
                        github_stats=stats,
                        date__lt=cutoff_date
                    ).delete()
                
                logger.info(f"GitHub stats updated for user {user.username}")
                try:
                    from .models import JobApplication
                    user_applications = JobApplication.objects.filter(user=user)
                    for application in user_applications:
                        was_verified = application.is_github_skills_verified
                        is_verified = application.verify_github_skills()
                        if was_verified != is_verified:
                            application.is_github_skills_verified = is_verified
                            application.save(update_fields=['is_github_skills_verified'])
                            logger.info(f"Updated GitHub skills verification for application {application.id}: {is_verified}")
                except Exception as e:
                    logger.error(f"Failed to update GitHub skills verification: {str(e)}")
                return True
            else:
                # Update with error
                GitHubStats.objects.update_or_create(
                    user=user,
                    defaults={
                        'username': username,
                        'github_url': github_link.url,
                        'fetch_status': 'failed',
                        'error_message': data.get('error', 'Unknown error'),
                        'last_fetched': timezone.now()
                    }
                )
                logger.error(f"Failed to fetch GitHub stats for {username}: {data.get('error')}")
                return False
                
        except Exception as e:
            logger.error(f"Error updating GitHub stats for user {user.username}: {str(e)}")
            try:
                from .models import GitHubStats
                GitHubStats.objects.update_or_create(
                    user=user,
                    defaults={
                        'fetch_status': 'failed',
                        'error_message': str(e),
                        'last_fetched': timezone.now()
                    }
                )
            except:
                pass
            return False
        finally:
            # Release lock
            cache.delete(lock_key)
    
    @staticmethod
    def update_stats_async(user):
        """Run update in background thread only if needed"""
        # Quick check before spawning thread
        if not GitHubStatsUpdater.needs_update(user):
            return None
            
        import threading
        thread = threading.Thread(
            target=GitHubStatsUpdater.update_github_stats,
            args=(user,)
        )
        thread.daemon = True
        thread.start()
        return thread