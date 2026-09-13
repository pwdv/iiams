import time
from django.core.management.base import BaseCommand
from simulation.engine import run_cycle


class Command(BaseCommand):
    help = 'Run the IIAMS simulation continuously as a background operations engine.'

    def add_arguments(self, parser):
        parser.add_argument('--interval', type=float, default=3.0, help='Seconds between simulation cycles.')
        parser.add_argument('--once', action='store_true', help='Run a single cycle and exit.')

    def handle(self, *args, **options):
        interval = max(0.25, options['interval'])
        self.stdout.write(self.style.SUCCESS(f'IIAMS live simulation started (every {interval:g}s). Press Ctrl+C to stop.'))
        try:
            while True:
                result = run_cycle()
                self.stdout.write(f"[{time.strftime('%H:%M:%S')}] {result.get('transactions', 0)} stock movements / {result['readings']} sensor readings / {result['events']} events", ending='\n')
                self.stdout.flush()
                if options['once']:
                    break
                time.sleep(interval)
        except KeyboardInterrupt:
            self.stdout.write(self.style.WARNING('IIAMS live simulation stopped.'))
