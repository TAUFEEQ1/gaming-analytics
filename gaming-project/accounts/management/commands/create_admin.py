"""
Management command to create admin accounts for Gaming Analytics
"""

from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
import getpass


class Command(BaseCommand):
    help = 'Create a new admin account for Gaming Analytics'

    def add_arguments(self, parser):
        parser.add_argument(
            '--username',
            type=str,
            help='Username for the new admin account',
        )
        parser.add_argument(
            '--email',
            type=str,
            help='Email for the new admin account',
        )
        parser.add_argument(
            '--first_name',
            type=str,
            help='First name for the new admin account',
        )
        parser.add_argument(
            '--last_name',
            type=str,
            help='Last name for the new admin account',
        )
        parser.add_argument(
            '--superuser',
            action='store_true',
            help='Create as superuser (full admin privileges)',
        )
        parser.add_argument(
            '--staff',
            action='store_true',
            help='Create as staff user (admin access but not superuser)',
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('🎮 Gaming Analytics - Admin Account Creator')
        )
        self.stdout.write('=' * 50)

        # Get username
        username = options.get('username')
        if not username:
            username = input('Username: ')

        # Check if username already exists
        if User.objects.filter(username=username).exists():
            raise CommandError(f'User "{username}" already exists.')

        # Get email
        email = options.get('email')
        if not email:
            email = input('Email address: ')

        # Get names
        first_name = options.get('first_name')
        if not first_name:
            first_name = input('First name (optional): ')

        last_name = options.get('last_name')
        if not last_name:
            last_name = input('Last name (optional): ')

        # Get password
        password = getpass.getpass('Password: ')
        password_confirm = getpass.getpass('Password (again): ')

        if password != password_confirm:
            raise CommandError('Passwords do not match.')

        if len(password) < 8:
            raise CommandError('Password must be at least 8 characters long.')

        # Determine user type
        is_superuser = options.get('superuser', False)
        is_staff = options.get('staff', False)

        if not is_superuser and not is_staff:
            user_type = input('User type (1=Staff, 2=Superuser): ')
            if user_type == '2':
                is_superuser = True
                is_staff = True
            elif user_type == '1':
                is_staff = True
            else:
                raise CommandError('Invalid user type. Choose 1 for Staff or 2 for Superuser.')
        elif is_superuser:
            is_staff = True  # Superusers are automatically staff

        try:
            # Create the user
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name,
            )
            
            user.is_staff = is_staff
            user.is_superuser = is_superuser
            user.save()

            # Success message
            user_type_str = 'superuser' if is_superuser else 'staff user'
            self.stdout.write(
                self.style.SUCCESS(f'✅ Successfully created {user_type_str}: {username}')
            )
            
            self.stdout.write(
                self.style.SUCCESS(f'📧 Email: {email}')
            )
            
            if first_name or last_name:
                full_name = f"{first_name} {last_name}".strip()
                self.stdout.write(
                    self.style.SUCCESS(f'👤 Name: {full_name}')
                )

            self.stdout.write('\n' + '=' * 50)
            self.stdout.write(
                self.style.SUCCESS('🚀 Account created! You can now log in to the admin interface.')
            )
            self.stdout.write(
                self.style.SUCCESS('📍 Admin URL: http://localhost:8000/admin/')
            )

        except ValidationError as e:
            raise CommandError(f'Validation error: {e}')
        except Exception as e:
            raise CommandError(f'Error creating user: {e}')