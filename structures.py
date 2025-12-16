"""
EdukaTrack Custom Data Structures Module

This module implements custom data structures as specified in the project proposal
for the educational tracking system. These structures provide efficient operations
for managing students, enrollments, schedules, grades, and other academic data.

Data Structures Implemented:
- EnrollmentQueue: FIFO queue for processing enrollment requests fairly
- DynamicArray: Flexible array for grade records with sorting/filtering
- ConflictSet: Set-based conflict detection for schedule management
- HashMap: O(1) key-value storage for sessions and caching
- UniqueIDSet: Ensures unique school IDs for students/teachers
- StudentList: Linked list for ordered student record management

See PSEUDOCODE.md for detailed algorithm documentation.

Author: EdukaTrack Development Team
Version: 1.0.0
"""

import collections


class EnrollmentQueue:
    """
    Queue data structure for managing enrollment requests (FIFO).
    
    Ensures fair processing of student enrollment requests by maintaining
    first-in-first-out order. Admin processes requests in the order received.
    
    Time Complexity:
        - enqueue: O(1)
        - dequeue: O(1) using deque
        - peek: O(1)
        - search: O(n)
    
    Usage:
        queue = EnrollmentQueue()
        queue.enqueue(request_id)
        oldest_request = queue.dequeue()
    """
    
    def __init__(self):
        self.queue = collections.deque()
    
    def enqueue(self, enrollment_id):
        """Add an enrollment request to the back of the queue"""
        self.queue.append(enrollment_id)
    
    def dequeue(self):
        """Remove and return the front enrollment request"""
        if not self.is_empty():
            return self.queue.popleft()
        return None
    
    def peek(self):
        """View the front enrollment request without removing"""
        return self.queue[0] if not self.is_empty() else None
    
    def is_empty(self):
        """Check if queue is empty"""
        return len(self.queue) == 0

    def size(self):
        """Return the number of items in the queue"""
        return len(self.queue)
    
    def traverse(self):
        """Traverse and return all items in the queue as a list"""
        return list(self.queue)
    
    def search(self, enrollment_id):
        """Search for an enrollment request in the queue"""
        return enrollment_id in self.queue
    
    def remove(self, enrollment_id):
        """Remove a specific enrollment request from the queue"""
        if enrollment_id in self.queue:
            self.queue.remove(enrollment_id)
            return True
        return False

class DynamicArray:
    """
    Dynamic array for storing collections of related data with sorting.
    
    Primary use case is managing grade records with flexible sorting
    by score, name, date, or any other key. Supports filtering operations
    for displaying subsets of data.
    
    Time Complexity:
        - add: O(1) amortized
        - sort_by_grade: O(n log n)
        - calculate_average: O(n)
        - search: O(n)
        - filter_by: O(n)
    
    Usage:
        grades = DynamicArray()
        grades.add({'student': 'Alice', 'score': 92})
        grades.sort_by_grade(reverse=True)
        avg = grades.calculate_average()
    """
    
    def __init__(self):
        self.array = []

    def add(self, element):
        """Insert an element at the end of the list"""
        self.array.append(element)

    def get_all(self):
        """Return all elements in the list"""
        return self.array

    def sort_by_grade(self, reverse=True):
        """Sort the list by grade score"""
        self.array.sort(key=lambda x: x.get('score', 0) or 0, reverse=reverse)
    
    def sort_by_key(self, key, reverse=False):
        """Sort the list by any key"""
        self.array.sort(key=lambda x: x.get(key, 0), reverse=reverse)
    
    def calculate_average(self):
        """Calculate the average score of all items"""
        if not self.array:
            return 0.0
        scores = [float(item.get('score', 0) or 0) for item in self.array]
        return round(sum(scores) / len(scores), 2) if scores else 0.0
    
    def insert(self, index, element):
        """Insert an element at a specific index"""
        self.array.insert(index, element)
    
    def delete(self, element):
        """Delete an element from the list"""
        if element in self.array:
            self.array.remove(element)
    
    def delete_by_key(self, key, value):
        """Delete an element by key-value match"""
        self.array = [item for item in self.array if item.get(key) != value]
    
    def search(self, key, value):
        """Search for an element by key-value"""
        return next((item for item in self.array if item.get(key) == value), None)
    
    def filter_by(self, key, value):
        """Filter and return all elements matching key-value"""
        return [item for item in self.array if item.get(key) == value]
    
    def traverse(self):
        """Traverse and return all elements"""
        return [item for item in self.array]
    
    def clear(self):
        """Clear all elements from the list"""
        self.array = []
    
    def size(self):
        """Return the number of elements"""
        return len(self.array)

class ConflictSet:
    """
    Set data structure for managing schedule slots and detecting conflicts.
    
    Uses hash set for O(1) conflict detection when adding new schedules.
    Prevents double-booking of rooms, teachers, or time slots.
    
    Time Complexity:
        - add_schedule: O(1)
        - has_conflict: O(1)
        - remove_schedule: O(1)
    
    Usage:
        conflict_set = ConflictSet()
        if not conflict_set.has_conflict('MWF', '09:00-10:30'):
            conflict_set.add_schedule('MWF', '09:00-10:30')
    """
    
    def __init__(self):
        self.conflicts = set()

    def add_schedule(self, day, time_range):
        """Add a schedule slot (throws error if conflict exists)"""
        key = f"{day}:{time_range}"
        if key in self.conflicts:
            raise ValueError("Schedule conflict")
        self.conflicts.add(key)

    def has_conflict(self, day, time_range):
        """Check if a schedule slot already exists"""
        return f"{day}:{time_range}" in self.conflicts
    
    def remove_schedule(self, day, time_range):
        """Remove a schedule slot"""
        key = f"{day}:{time_range}"
        self.conflicts.discard(key)
    
    def traverse(self):
        """Traverse and return all schedule slots"""
        return list(self.conflicts)
    
    def clear(self):
        """Clear all schedule slots"""
        self.conflicts = set()
    
    def size(self):
        """Return the number of schedule slots"""
        return len(self.conflicts)
    
    def add_unique(self, item):
        """Add a unique item to the set"""
        self.conflicts.add(item)
    
    def contains(self, item):
        """Check if item exists in the set"""
        return item in self.conflicts
    
    def remove_item(self, item):
        """Remove an item from the set"""
        self.conflicts.discard(item)

class HashMap:
    """
    Hash map for fast O(1) key-value lookups.
    
    Primary uses:
    - Session token storage for authentication
    - Caching frequently accessed data
    - ID-to-object mappings for quick retrieval
    
    Time Complexity:
        - put: O(1) average
        - get: O(1) average
        - remove: O(1) average
        - contains: O(1) average
    
    Usage:
        sessions = HashMap()
        sessions.put(token, session_data)
        session = sessions.get(token)
    """
    
    def __init__(self):
        self.data = {}
    
    def put(self, key, value):
        """Insert or update a key-value pair"""
        self.data[key] = value
    
    def get(self, key, default=None):
        """Get value by key, return default if not found"""
        return self.data.get(key, default)
    
    def remove(self, key):
        """Remove a key-value pair"""
        if key in self.data:
            del self.data[key]
            return True
        return False
    
    def contains(self, key):
        """Check if key exists"""
        return key in self.data
    
    def keys(self):
        """Return all keys"""
        return list(self.data.keys())
    
    def values(self):
        """Return all values"""
        return list(self.data.values())
    
    def items(self):
        """Return all key-value pairs"""
        return list(self.data.items())
    
    def size(self):
        """Return the number of entries"""
        return len(self.data)
    
    def clear(self):
        """Clear all entries"""
        self.data = {}
    
    def traverse(self):
        """Traverse and return all entries as a list of tuples"""
        return [(k, v) for k, v in self.data.items()]
    
    def update(self, other_dict):
        """Update with another dictionary"""
        self.data.update(other_dict)
    
    def search_by_value(self, value):
        """Search for key by value"""
        for k, v in self.data.items():
            if v == value:
                return k
        return None

class UniqueIDSet:
    """
    Set for maintaining unique identifiers.
    
    Ensures no duplicate school IDs for students or teachers.
    Used during registration to generate unique IDs and during
    validation to check for existing IDs.
    
    Time Complexity:
        - add: O(1) average
        - contains: O(1) average
        - remove: O(1) average
        - generate_id: O(1) amortized
    
    Usage:
        id_set = UniqueIDSet()
        if not id_set.contains('STU-2024-00001'):
            id_set.add('STU-2024-00001')
    """
    
    def __init__(self):
        self.ids = set()
    
    def add(self, id_value):
        """Add a unique ID, returns False if already exists"""
        if id_value in self.ids:
            return False
        self.ids.add(id_value)
        return True
    
    def remove(self, id_value):
        """Remove an ID"""
        if id_value in self.ids:
            self.ids.discard(id_value)
            return True
        return False
    
    def contains(self, id_value):
        """Check if ID exists"""
        return id_value in self.ids
    
    def get_all(self):
        """Return all IDs as a list"""
        return list(self.ids)
    
    def size(self):
        """Return the count of unique IDs"""
        return len(self.ids)
    
    def clear(self):
        """Clear all IDs"""
        self.ids = set()
    
    def traverse(self):
        """Traverse and return all IDs"""
        return list(self.ids)

class StudentList:
    """
    Specialized list for managing student collections.
    
    Provides student-specific operations like filtering by program,
    sorting by name or year level, and searching by ID.
    
    Time Complexity:
        - add_student: O(1)
        - remove_student: O(n)
        - get_student: O(n)
        - sort_by_name: O(n log n)
        - filter_by_program: O(n)
    
    Usage:
        students = StudentList()
        students.add_student({'id': 1, 'name': 'Alice', 'program_id': 1})
        students.sort_by_name()
        cs_students = students.filter_by_program(program_id=1)
    """
    
    def __init__(self):
        self.students = []
    
    def add_student(self, student_data):
        """Add a student to the list"""
        self.students.append(student_data)
    
    def remove_student(self, student_id):
        """Remove a student by ID"""
        self.students = [s for s in self.students if s.get('id') != student_id]
    
    def get_student(self, student_id):
        """Get a student by ID"""
        return next((s for s in self.students if s.get('id') == student_id), None)
    
    def get_all(self):
        """Return all students"""
        return self.students
    
    def sort_by_name(self):
        """Sort students by name"""
        self.students.sort(key=lambda x: x.get('name', ''))
    
    def sort_by_year(self):
        """Sort students by year level"""
        self.students.sort(key=lambda x: x.get('year_level', 0))
    
    def filter_by_program(self, program_id):
        """Filter students by program"""
        return [s for s in self.students if s.get('program_id') == program_id]
    
    def filter_by_status(self, status):
        """Filter students by status"""
        return [s for s in self.students if s.get('status') == status]
    
    def count(self):
        """Return the number of students"""
        return len(self.students)
    
    def traverse(self):
        """Traverse and return all students"""
        return [s for s in self.students]
    
    def clear(self):
        """Clear all students"""
        self.students = []
