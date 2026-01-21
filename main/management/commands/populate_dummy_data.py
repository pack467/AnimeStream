# main/management/commands/populate_dummy_data.py
"""
Management command untuk mengisi data dummy
Usage: python manage.py populate_dummy_data
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
import random

from main.models import Anime, AnimeViewLog, EpisodeRelease


class Command(BaseCommand):
    help = 'Populate dummy data for testing (views and episodes)'

    def handle(self, *args, **options):
        self.stdout.write('Starting to populate dummy data...')
        
        # Ambil semua anime
        all_anime = list(Anime.objects.all())
        
        if not all_anime:
            self.stdout.write(self.style.ERROR('No anime found in database. Please import anime data first.'))
            return
        
        self.stdout.write(f'Found {len(all_anime)} anime in database')
        
        # 1. Populate AnimeViewLog (untuk Top Views)
        self.stdout.write('Creating view logs...')
        now = timezone.now()
        
        view_logs_created = 0
        for anime in all_anime[:50]:  # ambil 50 anime pertama
            # Random views dalam 30 hari terakhir
            num_views = random.randint(100, 5000)
            
            for _ in range(num_views):
                # Random timestamp dalam 30 hari terakhir
                days_ago = random.randint(0, 30)
                hours_ago = random.randint(0, 23)
                viewed_at = now - timedelta(days=days_ago, hours=hours_ago)
                
                AnimeViewLog.objects.create(
                    anime=anime,
                    viewed_at=viewed_at
                )
                view_logs_created += 1
        
        self.stdout.write(self.style.SUCCESS(f'Created {view_logs_created} view logs'))
        
        # 2. Populate EpisodeRelease (untuk Today widget)
        self.stdout.write('Creating episode releases...')
        
        episodes_created = 0
        for anime in all_anime[:30]:  # ambil 30 anime pertama
            # Buat 5-10 episode untuk setiap anime
            num_episodes = random.randint(5, 10)
            
            for ep_num in range(1, num_episodes + 1):
                # Random release date dalam 7 hari terakhir
                hours_ago = random.randint(1, 168)  # 1-168 jam (7 hari)
                released_at = now - timedelta(hours=hours_ago)
                
                EpisodeRelease.objects.create(
                    anime=anime,
                    episode=f"Episode {ep_num}",
                    released_at=released_at
                )
                episodes_created += 1
        
        self.stdout.write(self.style.SUCCESS(f'Created {episodes_created} episode releases'))
        
        # Summary
        self.stdout.write(self.style.SUCCESS('='*50))
        self.stdout.write(self.style.SUCCESS('Dummy data population completed!'))
        self.stdout.write(self.style.SUCCESS(f'Total view logs: {view_logs_created}'))
        self.stdout.write(self.style.SUCCESS(f'Total episode releases: {episodes_created}'))
        self.stdout.write(self.style.SUCCESS('='*50))