// Define Test object constructor
function ATest(properties) {
    // Assign properties to the test object
    for (const key in properties) {
        if (properties.hasOwnProperty(key)) {
            this[key] = properties[key];
        }
    }
}

ATest.prototype.getAssertions = function() {
    const meta = (this.hasOwnProperty('metadata') ? this['metadata'].split('\n') : []);
    let asserts = [];

    for(let i = 0; i < meta.length; i++) {
        if(meta[i].startsWith('JSON') || meta[i].startsWith('ASSERT'))
            asserts.push(meta[i]);
    }

    return asserts;
}

ATest.prototype.hasMeta = function(key) { 
    const meta = (this.hasOwnProperty('metadata') ? this['metadata'].split('\n') : []);
    for(let i = 0; i < meta.length; i++) {
        if(meta[i].startsWith(key))
            return true;
    }

    return false;
}


ATest.prototype.getGroup = function() {
    // Get my group so we can sort tests in groups
    return undefined;
}

ATest.prototype.jsonPath = function(dotPath, jsonData) {
    const parts = dotPath.split('.');
    let current = jsonData;

    for (const part of parts) {
        if(part == '' || part == '$')
            continue;
        if (current && current.hasOwnProperty(part)) {
            current = current[part];
        } else {
            return undefined; // or any default value you prefer
        }
    }
    return current;
}

ATest.prototype.countJsonPath = function(dotPath, jsonData) {
    let elem = this.jsonPath(dotPath, jsonData);

    return elem.length;
}

ATest.prototype.findJsonKey = function(targetKey, jsonData) {
    // Check if the input is an object or array
    
    if (typeof jsonData === 'object' && jsonData !== null) {
        for (let key in jsonData) {
            if (jsonData.hasOwnProperty(key)) {
                if (key === targetKey) {
                    //console.log('FiND' + targetKey + ' in ' + jsonData[key]);
                    return jsonData[key];  // Return the value if the key matches
                }
                // If the value is an object or array, recurse into it
                let result = this.findJsonKey(targetKey, jsonData[key]);
                if (result !== undefined) {
                    return result;  // Return the found value
                }
            }
        }
    }
    return undefined;  // Return undefined if the key is not found
}

// Add method to Test object prototype to execute the test
ATest.prototype.execute = function() {
    // Implement test execution logic here
    console.log(`Executing test '${this.name}'...`);
};

ATest.prototype.get = function(key) {
    return this[key];
}


// Example test data returned from the database
//const testDataFromDatabase = [
//    { id: 1, name: 'Test 1', method: 'GET', url: 'https://example.com/api', headers: {}, data: '', cookies: {} },
//    { id: 2, name: 'Test 2', method: 'POST', url: 'https://example.com/api', headers: {}, data: '', cookies: {} }
//];

/*
// Map database values to Test objects
const tests = testDataFromDatabase.map(test => {
    // Extract properties from the database record
    const properties = {
        id: test.id,
        name: test.name,
        method: test.method,
        url: test.url,
        headers: test.headers,
        data: test.data,
        cookies: test.cookies
    };
    // Create a new Test object with the extracted properties
    return new ATest(properties);
});

*/