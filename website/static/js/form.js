document.addEventListener("DOMContentLoaded", function() {
    const form = document.getElementById('new-employee-form');
    let formIsValid = true;
    const formErrors = document.getElementById('form-errors');

    const isFieldRequiredAndEmpty = (field) => {
        return field.hasAttribute('required') && !field.value.trim();
    };

    const validateFirstNameAndMiddle = (name) => /^[A-Za-z]+(?:\s[A-Za-z\.]+)?$/.test(name);
    const validateLastNameAndSuffix = (name) => /^[A-Za-z]+(?:\s(?:Jr\.|Sr\.|III|IV|V|VI|[A-Za-z]+))?$/.test(name);
    const validateEmail = (email) => /^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$/.test(email);
    const validatePhone = (phone) => /^\+?1?\s?\(?\d{3}\)?[-\s]?\d{3}[-\s]?\d{4}$/.test(phone);
    const validateAddress = (address) => /^\d+\s[A-Za-z\s]+(?:,\s[A-Za-z\s]+)*$/.test(address); // Updated for street address validation
    const validateZipCode = (zipcode) => /^\d{5}(-\d{4})?$/.test(zipcode);
    const validateCity = (city) => /^[A-Za-z\s]+$/.test(city); // Allow spaces for city names composed of two or more words
    const validateState = (state) => /^[A-Za-z\s]+$/.test(state); // Allow spaces for state names composed of two or more words

    const validators = {
        first_name: validateFirstNameAndMiddle,
        last_name: validateLastNameAndSuffix,
        email: validateEmail,
        phone: validatePhone,
        address: validateAddress,
        city: validateCity,
        state: validateState,
        zipcode: validateZipCode
    };

    const getErrorMessageForField = (fieldName) => {
    switch (fieldName) {
        case 'email':
            return 'Invalid email format. Example: name@example.com';
        case 'phone':
            return 'Invalid phone number. Format: +1 234-567-8900 or (234) 567-8900';
        case 'first_name':
            return 'Please enter a valid first name. If applicable, include middle initial or middle name. Example: John E.';
        case 'last_name':
            return 'Please enter a valid last name. If applicable, include suffixes (Jr., Sr., III). Example: Doe Jr.';
        case 'address':
            return 'Invalid address format. Include house number and street name. Example: 123 Main St';
        case 'city':
            return 'Please enter a valid city name. Only letters and spaces are allowed. Example: New York';
        case 'state':
            return 'Please enter a valid state name or abbreviation. Example: NY for New York';
        case 'zipcode':
            return 'Invalid ZIP code format. Use 5 digits or 5+4 format. Example: 12345 or 12345-6789';
        default:
            return 'This field is required.';
        }
    };

    const validateField = (field) => {
        if (isFieldRequiredAndEmpty(field)) {
            field.classList.add('is-invalid');
            const feedbackElement = field.nextElementSibling;
            feedbackElement.textContent = getErrorMessageForField(field.name);
            feedbackElement.style.display = 'block';
            formIsValid = false;
            return; // Exit the function if field is required but empty
        }

        // Proceed with other validations if the field is not empty
        const validator = validators[field.name];
        if (validator && !validator(field.value)) {
            field.classList.add('is-invalid');
            const feedbackElement = field.nextElementSibling;
            feedbackElement.textContent = getErrorMessageForField(field.name);
            feedbackElement.style.display = 'block';
            formIsValid = false;
        } else {
            field.classList.remove('is-invalid');
            field.nextElementSibling.style.display = 'none';
        }
    };

    document.querySelectorAll('input, select').forEach(field => {
        field.addEventListener('blur', () => validateField(field));
    });

    form.addEventListener('keydown', function(event) {
        if (event.key === 'Enter') {
            const activeElement = document.activeElement;
            const submitButton = form.querySelector('[type="submit"]');

            if (activeElement !== submitButton) {
                event.preventDefault(); // Prevent form submission

                // Mimic tab behavior - move focus to the next focusable element
                const focusableElements = 'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])';
                const focusables = Array.from(form.querySelectorAll(focusableElements)).filter(element => !element.disabled);

                const currentFocusIndex = focusables.indexOf(document.activeElement);
                const nextFocusIndex = (currentFocusIndex + 1) % focusables.length;

                focusables[nextFocusIndex].focus();
            }
            // If the submit button is focused, allow the default form submission
        }
    });

    form.addEventListener('submit', function(e) {
        e.preventDefault();
        formIsValid = true;

        document.querySelectorAll('input, select').forEach(field => {
            validateField(field);
        });

        if (!formIsValid) {
            alert('Please fill out all required fields and correct any errors before submitting.');
            return; // Prevent form submission if any field is invalid or empty
        }

        // Proceed with form submission if valid
        submitFormData();
    });

    function submitFormData() {
        const formData = new FormData(form);
        const url = form.action;
        const options = {
            method: 'POST',
            body: formData,
        };

        fetch(url, options)
            .then(response => {
                if (!response.ok) {
                    throw new Error('Network response was not ok: ' + response.statusText);
                }
                return response.json();
            })
            .then(data => {
                console.log('Success:', data);
                alert('Form submitted successfully!');
                form.reset();
                window.location.href = '/submission-success'; // Redirect on success
            })
            .catch((error) => {
                console.error('Error:', error);
                alert('An error occurred while submitting the form. Please try again.');
            });
    }

// Global error listener
window.addEventListener('error', function(event) {
    console.error('Error caught:', event.message, 'at', event.filename, ':', event.lineno);
});

// Unhandled promise rejection listener
window.addEventListener('unhandledrejection', function(event) {
    console.error('Unhandled rejection:', event.reason);
});

});