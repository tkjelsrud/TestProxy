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
        if(meta[i].startsWith('JSON'))
            asserts.push(meta[i]);
    }

    return asserts;
}

ATest.prototype.jsonPath = function(dotPath, jsonData) {
    const parts = dotPath.split('.');
    let current = jsonData;

    for (const part of parts) {
        console.log(current);
        console.log('part:' + part);
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