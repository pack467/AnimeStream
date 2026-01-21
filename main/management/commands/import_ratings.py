# main/management/commands/import_ratings.py
"""
Django management command untuk import data rating dari Excel

Usage:
    python manage.py import_ratings [path_to_excel]
    
    atau (default path):
    python manage.py import_ratings

File akan dicari di:
    1. Path yang diberikan
    2. Current directory
    3. /mnt/user-data/uploads/
    4. Project root
"""

import pandas as pd
import numpy as np
from pathlib import Path
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User
from django.db.models import Avg
from main.models import Anime, UserAnimeRating


class Command(BaseCommand):
    help = 'Import rating data from Excel file to database'
    
    def add_arguments(self, parser):
        parser.add_argument(
            'excel_file',
            nargs='?',
            type=str,
            default='Data_setelah_pra-processing.xlsx',
            help='Path to Excel file (default: Data_setelah_pra-processing.xlsx)'
        )
        
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing ratings before import'
        )
        
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be imported without actually importing'
        )
    
    def handle(self, *args, **options):
        excel_file = options['excel_file']
        clear_existing = options['clear']
        dry_run = options['dry_run']
        
        self.stdout.write("=" * 80)
        self.stdout.write(self.style.SUCCESS("IMPORT DATA RATING DARI EXCEL KE DATABASE"))
        self.stdout.write("=" * 80)
        
        if dry_run:
            self.stdout.write(self.style.WARNING("🔍 DRY RUN MODE - No data will be saved"))
        
        # ============================================================================
        # Find Excel file
        # ============================================================================
        excel_path = self.find_excel_file(excel_file)
        
        if not excel_path:
            raise CommandError(f"❌ File '{excel_file}' not found!")
        
        self.stdout.write(f"📂 File: {excel_path}")
        
        # ============================================================================
        # Clear existing data if requested
        # ============================================================================
        if clear_existing and not dry_run:
            self.stdout.write("\n⚠️  Clearing existing ratings...")
            deleted_count = UserAnimeRating.objects.all().delete()[0]
            self.stdout.write(self.style.WARNING(f"   Deleted {deleted_count} existing ratings"))
        
        # ============================================================================
        # Load Excel
        # ============================================================================
        self.stdout.write("\n" + "=" * 80)
        self.stdout.write("STEP 1: LOAD DATA EXCEL")
        self.stdout.write("=" * 80)
        
        try:
            df = pd.read_excel(excel_path)
            self.stdout.write(self.style.SUCCESS("✅ Data loaded successfully"))
            self.stdout.write(f"   - Shape: {df.shape}")
            self.stdout.write(f"   - Users: {len(df)}")
            self.stdout.write(f"   - Anime columns: {len(df.columns) - 1}")
        except Exception as e:
            raise CommandError(f"❌ Failed to load Excel: {e}")
        
        # ============================================================================
        # Prepare data
        # ============================================================================
        self.stdout.write("\n" + "=" * 80)
        self.stdout.write("STEP 2: PREPARE DATA")
        self.stdout.write("=" * 80)
        
        user_names = df['user_name'].tolist()
        anime_titles = [col for col in df.columns if col != 'user_name']
        
        self.stdout.write(self.style.SUCCESS("✅ Data prepared"))
        self.stdout.write(f"   - User names: {len(user_names)}")
        self.stdout.write(f"   - Anime titles: {len(anime_titles)}")
        
        # ============================================================================
        # Create/Get Users
        # ============================================================================
        self.stdout.write("\n" + "=" * 80)
        self.stdout.write("STEP 3: CREATE OR GET USERS")
        self.stdout.write("=" * 80)
        
        users_map, users_created, users_existing = self.process_users(
            user_names, dry_run
        )
        
        self.stdout.write(self.style.SUCCESS("✅ Users processed"))
        self.stdout.write(f"   - Created: {users_created}")
        self.stdout.write(f"   - Existing: {users_existing}")
        self.stdout.write(f"   - Total: {len(users_map)}")
        
        # ============================================================================
        # Create/Get Anime
        # ============================================================================
        self.stdout.write("\n" + "=" * 80)
        self.stdout.write("STEP 4: CREATE OR GET ANIME")
        self.stdout.write("=" * 80)
        
        anime_map, anime_created, anime_existing = self.process_anime(
            anime_titles, dry_run
        )
        
        self.stdout.write(self.style.SUCCESS("✅ Anime processed"))
        self.stdout.write(f"   - Created: {anime_created}")
        self.stdout.write(f"   - Existing: {anime_existing}")
        self.stdout.write(f"   - Total: {len(anime_map)}")
        
        # ============================================================================
        # Import Ratings
        # ============================================================================
        self.stdout.write("\n" + "=" * 80)
        self.stdout.write("STEP 5: IMPORT RATINGS")
        self.stdout.write("=" * 80)
        
        stats = self.import_ratings(
            df, users_map, anime_map, anime_titles, dry_run
        )
        
        self.stdout.write(self.style.SUCCESS("\n✅ Ratings imported"))
        self.stdout.write(f"   - Created: {stats['created']}")
        self.stdout.write(f"   - Updated: {stats['updated']}")
        self.stdout.write(f"   - Skipped (NaN): {stats['skipped']}")
        self.stdout.write(f"   - Total: {stats['created'] + stats['updated']}")
        
        # ============================================================================
        # Update Anime Total Rating
        # ============================================================================
        if not dry_run:
            self.stdout.write("\n" + "=" * 80)
            self.stdout.write("STEP 6: UPDATE ANIME TOTAL RATING")
            self.stdout.write("=" * 80)
            
            anime_updated = self.update_anime_ratings()
            self.stdout.write(self.style.SUCCESS(f"✅ Anime total_rating updated: {anime_updated}"))
        
        # ============================================================================
        # Statistics
        # ============================================================================
        self.stdout.write("\n" + "=" * 80)
        self.stdout.write("STEP 7: STATISTICS")
        self.stdout.write("=" * 80)
        
        self.show_statistics()
        
        # ============================================================================
        # Verify
        # ============================================================================
        if not dry_run:
            self.stdout.write("\n" + "=" * 80)
            self.stdout.write("STEP 8: VERIFY PIVOT MATRIX")
            self.stdout.write("=" * 80)
            
            self.verify_pivot_matrix()
        
        # ============================================================================
        # Summary
        # ============================================================================
        self.stdout.write("\n" + "=" * 80)
        self.stdout.write(self.style.SUCCESS("IMPORT COMPLETED!"))
        self.stdout.write("=" * 80)
        
        if dry_run:
            self.stdout.write(self.style.WARNING("\n⚠️  This was a DRY RUN - no data was saved"))
            self.stdout.write("   Run without --dry-run to actually import data")
        else:
            self.stdout.write(self.style.SUCCESS("\n✅ Data import selesai!"))
            self.stdout.write("\nNext steps:")
            self.stdout.write("  1. Verify data in admin: /admin/")
            self.stdout.write("  2. Test recommendations: python manage.py shell < test_svd_recommender.py")
            self.stdout.write("  3. Run server: python manage.py runserver")
    
    def find_excel_file(self, filename):
        """Find Excel file in various locations"""
        possible_paths = [
            Path(filename),
            Path.cwd() / filename,
            Path('/mnt/user-data/uploads') / filename,
            Path(__file__).parent.parent.parent.parent / filename,
        ]
        
        for path in possible_paths:
            if path.exists():
                return path
        
        return None
    
    def clean_anime_title(self, title):
        """Clean anime title for title_clean field"""
        import re
        s = str(title).lower().strip()
        s = re.sub(r"\s+", " ", s)
        s = re.sub(r"[^\w\s:!()\-.,'&/]+", "", s)
        return s.strip()
    
    def process_users(self, user_names, dry_run=False):
        """Create or get users"""
        users_map = {}
        users_created = 0
        users_existing = 0
        
        for username in user_names:
            username_clean = str(username).strip()
            
            if not username_clean or username_clean == 'nan':
                continue
            
            if dry_run:
                # Just check if exists
                if User.objects.filter(username=username_clean).exists():
                    users_existing += 1
                else:
                    users_created += 1
                users_map[username_clean] = None
            else:
                user, created = User.objects.get_or_create(
                    username=username_clean,
                    defaults={
                        'email': f'{username_clean}@example.com',
                        'is_active': True,
                    }
                )
                
                if created:
                    user.set_password('defaultpassword123')
                    user.save()
                    users_created += 1
                else:
                    users_existing += 1
                
                users_map[username_clean] = user
        
        return users_map, users_created, users_existing
    
    def process_anime(self, anime_titles, dry_run=False):
        """Create or get anime"""
        anime_map = {}
        anime_created = 0
        anime_existing = 0
        
        for anime_title in anime_titles:
            anime_title_clean = self.clean_anime_title(anime_title)
            
            if dry_run:
                if Anime.objects.filter(title=anime_title).exists():
                    anime_existing += 1
                else:
                    anime_created += 1
                anime_map[anime_title] = None
            else:
                anime, created = Anime.objects.get_or_create(
                    title=anime_title,
                    defaults={
                        'title_clean': anime_title_clean,
                        'total_rating': 0.0,
                        'genre': '',
                        'total_episode': '',
                        'anime_type': 'TV',
                        'year_release': '',
                        'content_rating': '',
                        'status': '',
                        'cover': 'default.jpg',
                        'wallpaper': '',
                    }
                )
                
                if created:
                    anime_created += 1
                else:
                    anime_existing += 1
                
                anime_map[anime_title] = anime
        
        return anime_map, anime_created, anime_existing
    
    def import_ratings(self, df, users_map, anime_map, anime_titles, dry_run=False):
        """Import ratings from DataFrame"""
        stats = {
            'created': 0,
            'updated': 0,
            'skipped': 0,
        }
        
        for idx, row in df.iterrows():
            username = str(row['user_name']).strip()
            
            if username not in users_map:
                continue
            
            user = users_map[username]
            
            for anime_title in anime_titles:
                rating_value = row[anime_title]
                
                if pd.isna(rating_value):
                    stats['skipped'] += 1
                    continue
                
                try:
                    rating_float = float(rating_value)
                except (ValueError, TypeError):
                    stats['skipped'] += 1
                    continue
                
                if rating_float < 1.0 or rating_float > 10.0:
                    stats['skipped'] += 1
                    continue
                
                if anime_title not in anime_map:
                    stats['skipped'] += 1
                    continue
                
                anime = anime_map[anime_title]
                
                if dry_run:
                    # Check if would create or update
                    if UserAnimeRating.objects.filter(user=user, anime=anime).exists():
                        stats['updated'] += 1
                    else:
                        stats['created'] += 1
                else:
                    rating_obj, created = UserAnimeRating.objects.update_or_create(
                        user=user,
                        anime=anime,
                        defaults={'rating': rating_float}
                    )
                    
                    if created:
                        stats['created'] += 1
                    else:
                        stats['updated'] += 1
            
            if (idx + 1) % 5 == 0:
                self.stdout.write(f"   Processed {idx + 1}/{len(df)} users...")
        
        return stats
    
    def update_anime_ratings(self):
        """Update anime total_rating with average"""
        anime_updated = 0
        
        for anime in Anime.objects.all():
            avg_rating = UserAnimeRating.objects.filter(anime=anime).aggregate(
                avg=Avg('rating')
            )['avg']
            
            if avg_rating:
                anime.total_rating = round(avg_rating, 2)
                anime.save(update_fields=['total_rating'])
                anime_updated += 1
        
        return anime_updated
    
    def show_statistics(self):
        """Show database statistics"""
        total_users = User.objects.count()
        total_anime = Anime.objects.count()
        total_ratings = UserAnimeRating.objects.count()
        
        if total_users > 0 and total_anime > 0:
            density = (total_ratings / (total_users * total_anime)) * 100
            
            self.stdout.write("Database Statistics:")
            self.stdout.write(f"   - Total users: {total_users}")
            self.stdout.write(f"   - Total anime: {total_anime}")
            self.stdout.write(f"   - Total ratings: {total_ratings}")
            self.stdout.write(f"   - Matrix density: {density:.2f}%")
            self.stdout.write(f"   - Avg ratings per user: {total_ratings/total_users:.1f}")
            self.stdout.write(f"   - Avg ratings per anime: {total_ratings/total_anime:.1f}")
            
            # Sample
            self.stdout.write("\n   Sample ratings:")
            sample_ratings = UserAnimeRating.objects.select_related('user', 'anime')[:5]
            for r in sample_ratings:
                self.stdout.write(f"   - {r.user.username} rated {r.anime.title}: {r.rating}")
    
    def verify_pivot_matrix(self):
        """Verify pivot matrix can be built"""
        try:
            from main.recommender import build_pivot_matrix
            
            pivot_df, user_ids, anime_objects = build_pivot_matrix()
            
            if pivot_df is not None:
                self.stdout.write(self.style.SUCCESS("✅ Pivot matrix successfully built"))
                self.stdout.write(f"   - Shape: {pivot_df.shape}")
                self.stdout.write(f"   - Users: {len(user_ids)}")
                self.stdout.write(f"   - Anime: {len(anime_objects)}")
                sparsity = (pivot_df.isna().sum().sum() / (pivot_df.shape[0] * pivot_df.shape[1]) * 100)
                self.stdout.write(f"   - Sparsity: {sparsity:.1f}%")
                self.stdout.write(self.style.SUCCESS("\n   ✅ Ready for SVD recommendations!"))
            else:
                self.stdout.write(self.style.WARNING("   ⚠️  Pivot matrix is empty"))
        except Exception as e:
            self.stdout.write(self.style.WARNING(f"   ⚠️  Could not verify: {e}"))