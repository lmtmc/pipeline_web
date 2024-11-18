var dagfuncs = window.dashAgGridFunctions = window.dashAgGridFunctions || {};

dagfuncs.CheckboxSelector = class {
    init(params) {
        // Create a container for the checkboxes in a 4x4 grid
        this.eContainer = document.createElement('div');
        // this.eContainer.classList.add('checkbox-grid-container');
        this.eContainer.classList.add('checkbox-container');
        this.eContainer.style.display = 'grid';          // Enable grid layout
        this.eContainer.style.gridTemplateColumns = 'repeat(4, 1fr)';  // Create 4 columns
        this.eContainer.style.gap = '2px';  // Space between checkboxes

        this.checkboxes = [];
        for (let i = 0; i < 16; i++) {
            // Create each checkbox with a label
            let checkboxLabel = document.createElement('label');
            checkboxLabel.style.display = 'flex';
            checkboxLabel.style.alignItems = 'center';   // Vertically align the label and checkbox
            checkboxLabel.style.justifyContent = 'center'; // Center the label

            let checkbox = document.createElement('input');
            checkbox.type = 'checkbox';
            checkbox.value = i;
            checkbox.checked = params.value && params.value.includes(i);

            checkbox.addEventListener('change', () => this.onCheckboxChange(params));
            this.checkboxes.push(checkbox);

            checkboxLabel.appendChild(checkbox);
            checkboxLabel.appendChild(document.createTextNode(i.toString()));
            this.eContainer.appendChild(checkboxLabel);
        }

        // Add a keydown event listener for Enter key to save changes
        this.eContainer.addEventListener('keydown', (event) => {
            if (event.key === 'Enter') {
                this.onEnterPressed(params);
            }
        });
    }

    // Update selected values when checkboxes change
    onCheckboxChange(params) {
        params.value = this.getSelectedValues();
    }

    // Get all selected checkbox values
    getSelectedValues() {
        return this.checkboxes
            .filter(checkbox => checkbox.checked)
            .map(checkbox => parseInt(checkbox.value));
    }
    getValue() {
        return this.getSelectedValues();
    }
    // Display the container (grid of checkboxes) as the cell editor
    getGui() {
        return this.eContainer;
    }

    afterGuiAttached() {
        this.eContainer.focus();  // Focus the container for keyboard events
    }

    destroy() {
        this.checkboxes.forEach(checkbox => checkbox.removeEventListener('change', this.onCheckboxChange));
    }

    isPopup() {
        return true;
    }

    onEnterPressed(params) {
        // Convert selected values to a comma-separated string
        params.value = this.getSelectedValues().join(", ");
        params.api.stopEditing();  // Stop editing mode to hide checkboxes
    }
};

dagfuncs.RadioSelector = class {
    init(params) {
        // Create the container div for the radio buttons
        this.eContainer = document.createElement('div');
        this.eContainer.classList.add('radio-container');

        // Set grid layout to center content with 2 columns
        this.eContainer.style.display = 'grid';
        this.eContainer.style.gridTemplateColumns = 'repeat(2, 1fr)';
        this.eContainer.style.gap = '2px';

        // Define available options for radio buttons, including "No Selection" at the beginning
        const values = [...(params.colDef.cellEditorParams.values || []), "Not Apply"];

        // Create radio buttons for each option
        this.radios = values.map((value) => {
            let radioLabel = document.createElement('label');

            // Add radio button
            let radio = document.createElement('input');
            radio.type = 'radio';
            radio.value = value;
            radio.name = `radio-${params.column.colId}`;
            // Remove default selection by not checking any radio button initially
            radio.checked = (params.value === value) && value !== "Not Apply";

            // Add listener to update the selected value
            radio.addEventListener('change', () => this.onRadioChange(params));

            radioLabel.appendChild(radio);
            radioLabel.appendChild(document.createTextNode(value.toString()));
            this.eContainer.appendChild(radioLabel);

            return radio;
        });
    }

    // Handle radio button change
    onRadioChange(params) {
        params.value = this.getSelectedValue();
        if (params.api) {
            params.api.stopEditing(); // Stop editing mode when selection is made
        }
    }

    // Get the selected radio value
    getSelectedValue() {
        // If "No Selection" is chosen, return null, otherwise return the selected value
        const selected = this.radios.find(radio => radio.checked)?.value || null;
        return selected === "Not Apply" ? null : selected;
    }

    getValue() {
        return this.getSelectedValue();
    }

    getGui() {
        return this.eContainer;
    }

    afterGuiAttached() {
        this.eContainer.focus();
    }

    destroy() {
        this.radios.forEach(radio => radio.removeEventListener('change', this.onRadioChange));
    }

    isPopup() {
        return false;
    }
};
class CustomMultiSelectCellEditor {
    init(params) {
        this.params = params;
        this.options = params.options || [];
        this.selectedValues = params.value || [];

        // Create a wrapper div
        this.eGui = document.createElement('div');
        this.eGui.style.padding = '5px';
        this.eGui.style.border = '1px solid #ccc';
        this.eGui.style.borderRadius = '4px';
        this.eGui.style.background = '#fff';

        // Create checkboxes for each option
        this.options.forEach(option => {
            const checkboxWrapper = document.createElement('div');
            checkboxWrapper.style.marginBottom = '5px';

            const checkbox = document.createElement('input');
            checkbox.type = 'checkbox';
            checkbox.value = option;
            checkbox.checked = this.selectedValues.includes(option);

            const label = document.createElement('label');
            label.innerText = option;
            label.style.marginLeft = '5px';

            checkboxWrapper.appendChild(checkbox);
            checkboxWrapper.appendChild(label);
            this.eGui.appendChild(checkboxWrapper);

            checkbox.addEventListener('change', (e) => {
                if (e.target.checked) {
                    this.selectedValues.push(option);
                } else {
                    this.selectedValues = this.selectedValues.filter(v => v !== option);
                }
            });
        });
    }
    getGui() {
        return this.eGui;
    }
    getValue() {
        return this.selectedValues;
    }
}
