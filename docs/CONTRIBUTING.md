# Contributing to Romualdez Skin and Eye Clinic Management System

Thank you for considering contributing to this project! This document provides guidelines for contributing to the codebase.

## Getting Started

1. **Fork the repository** on GitHub
2. **Clone your fork** locally:
   ```bash
   git clone https://github.com/YOUR-USERNAME/Romualdez-Skin-and-Eye-Clinic.git
   cd Romualdez-Skin-and-Eye-Clinic
   ```
3. **Set up the development environment** following the instructions in README.md
4. **Create a new branch** for your feature:
   ```bash
   git checkout -b feature/your-feature-name
   ```

## Development Workflow

### 1. Before Making Changes

- Pull the latest changes from the main branch:
  ```bash
  git checkout main
  git pull origin main
  ```
- Create a new feature branch:
  ```bash
  git checkout -b feature/descriptive-name
  ```

### 2. Making Changes

- Write clean, readable code
- Follow Django best practices
- Add comments for complex logic
- Update documentation if needed

### 3. Testing Your Changes

- Test all functionality manually
- Ensure no existing features are broken
- Test on different screen sizes (responsive design)
- Check the admin interface for any issues

### 4. Committing Changes

Use clear, descriptive commit messages:

```bash
git add .
git commit -m "Add feature: description of what you added"
```

**Good commit messages:**
- `Add patient search functionality to admin`
- `Fix billing calculation error`
- `Update appointment status colors`
- `Refactor inventory management views`

**Bad commit messages:**
- `Update`
- `Fix bug`
- `Changes`

### 5. Pushing Changes

```bash
git push origin feature/your-feature-name
```

### 6. Creating a Pull Request

1. Go to the repository on GitHub
2. Click "New Pull Request"
3. Select your feature branch
4. Fill in the PR template with:
   - Description of changes
   - Screenshots (if UI changes)
   - Testing performed
   - Any breaking changes

## Code Style Guidelines

### Python/Django

- Follow PEP 8 style guide
- Use meaningful variable and function names
- Maximum line length: 100 characters
- Use docstrings for functions and classes

```python
def calculate_total_bill(patient_id, services):
    """
    Calculate the total bill for a patient including all services.
    
    Args:
        patient_id (int): The ID of the patient
        services (list): List of service objects
        
    Returns:
        Decimal: Total bill amount
    """
    # Implementation here
    pass
```

### HTML/Templates

- Use proper indentation (4 spaces)
- Close all tags
- Use semantic HTML
- Include comments for complex sections

### CSS

- Use the existing CSS variable system
- Follow BEM naming convention where possible
- Group related styles together
- Add comments for complex styles

### JavaScript

- Use ES6+ syntax
- Add comments for complex logic
- Handle errors appropriately
- Test in multiple browsers

## Database Migrations

When making model changes:

1. Create migrations:
   ```bash
   python manage.py makemigrations
   ```

2. Review the migration file

3. Apply migrations:
   ```bash
   python manage.py migrate
   ```

4. **Always commit migration files** with your changes

## Adding New Features

### Models
- Add to `bookings/models.py`
- Include proper field types and validations
- Add `__str__` method for better admin display
- Add help_text for clarity

### Views
- Keep views simple and focused
- Use class-based views where appropriate
- Handle errors gracefully
- Add proper authentication/authorization

### Admin Interface
- Register new models in `bookings/admin.py`
- Customize list_display, search_fields, etc.
- Add filters and actions where helpful

### Templates
- Use template inheritance
- Keep templates DRY (Don't Repeat Yourself)
- Use template tags and filters appropriately

## Testing Checklist

Before submitting a PR, ensure:

- [ ] Code runs without errors
- [ ] All migrations are applied
- [ ] Static files are collected
- [ ] Admin interface works correctly
- [ ] Forms validate properly
- [ ] Responsive design works on mobile
- [ ] No console errors in browser
- [ ] All existing features still work

## Questions or Problems?

- Check existing issues on GitHub
- Create a new issue if needed
- Contact the development team

## License

By contributing, you agree that your contributions will be licensed under the same license as the project.

Thank you for contributing!
