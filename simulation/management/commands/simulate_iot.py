from django.core.management.base import BaseCommand
from simulation.engine import run_cycle


class Command(BaseCommand):
    help = 'Run one or more IIAMS IoT/business simulation cycles.'

    def add_arguments(self, parser):
        parser.add_argument('--cycles', type=int, default=1)

    def handle(self, *args, **options):
        for _ in range(max(1, options['cycles'])):
            result = run_cycle()
            self.stdout.write(self.style.SUCCESS(f"Cycle complete: {result['readings']} readings, {result['events']} events."))
