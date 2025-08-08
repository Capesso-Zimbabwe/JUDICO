from django.utils import timezone
from django.contrib.auth.models import User
from client_management.models import Client
from task_management.models import Task
import random
from datetime import timedelta

def create_sample_tasks():
    # Get all clients
    clients = list(Client.objects.all())
    if not clients:
        print("No clients found in the database. Please create some clients first.")
        return
    
    # Get all lawyers (users with lawyer_profile)
    lawyers = list(User.objects.filter(lawyer_profile__isnull=False))
    if not lawyers:
        print("No lawyers found in the database. Please create some lawyers first.")
        return
    
    # Get a staff user for created_by
    staff_users = list(User.objects.filter(is_staff=True))
    if not staff_users:
        print("No staff users found in the database. Please create a staff user first.")
        return
    
    created_by = random.choice(staff_users)
    
    # Task properties
    titles = [
        "Contract Review",
        "Case Research",
        "Client Meeting",
        "Document Preparation",
        "Court Filing",
        "Legal Analysis",
        "Deposition Preparation",
        "Settlement Negotiation",
        "Trial Preparation",
        "Legal Brief Writing",
        "Client Consultation"
    ]
    
    descriptions = [
        "Review and analyze the contract for legal compliance and potential issues.",
        "Conduct comprehensive research on case law relevant to the current litigation.",
        "Schedule and prepare for meeting with client to discuss case strategy.",
        "Prepare necessary legal documents for upcoming court filing.",
        "Submit required documents to the court before the deadline.",
        "Analyze legal implications of recent developments in the case.",
        "Prepare questions and strategy for upcoming deposition.",
        "Negotiate settlement terms with opposing counsel.",
        "Prepare exhibits, witnesses, and arguments for trial.",
        "Draft legal brief addressing key issues in the case.",
        "Initial consultation with new client to assess legal needs."
    ]
    
    statuses = [status[0] for status in Task.STATUS_CHOICES]
    priorities = [priority[0] for priority in Task.PRIORITY_CHOICES]
    
    # Create 11 tasks
    tasks_created = 0
    for i in range(11):
        # Generate a due date between today and 30 days from now
        due_date = timezone.now().date() + timedelta(days=random.randint(1, 30))
        
        # Create the task
        task = Task(
            title=titles[i],
            description=descriptions[i],
            client=random.choice(clients),
            assigned_to=random.choice(lawyers),
            created_by=created_by,
            status=random.choice(statuses),
            priority=random.choice(priorities),
            due_date=due_date
        )
        task.save()
        tasks_created += 1
        print(f"Created task: {task.title}")
    
    print(f"\nSuccessfully created {tasks_created} sample tasks.")

if __name__ == "__main__":
    print("Starting to create sample tasks...")
    create_sample_tasks()
    print("Script execution completed.")