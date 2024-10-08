// General variables for sizes and locations
let canvasWidth = 1024;
let canvasHeight = 1536;
let sectionSize = 512;
let labelSize = 32;
let textPadding = 10;
let rectPadding = 40;

// Noise scale variables for controlling the smoothness of the Perlin noise pattern
let xScale = 0.015;
let yScale = 0.02;

// Variables to control the gap and offset for Perlin noise
let gap = 20;  // Distance between circles in the grid
let offsetR = 100;  // Offset for Perlin noise in board R
let offsetA = 200;  // Offset for Perlin noise in board A

let drawing = [];  // Array to store the points from the sketch on the left side
let lastClickTime = 0;  // For double-click detection
let doubleClickThreshold = 300;  // Time threshold (in milliseconds) for double-click reset

function setup() {
  createCanvas(canvasWidth, canvasHeight);  // Adjust canvas size based on general variables
  background(255);  // Set background to white

  // Draw the borders and labels
  drawBoard();
  
  // Initial Perlin noise grid on the middle side (R)
  dotGridR();
  
  // Initial Perlin noise grid on the new board (A)
  dotGridA();
}

function draw() {
  // Draw on the left side ("L") while holding the mouse
  if (mouseIsPressed && mouseX <= sectionSize && mouseY <= sectionSize) {  // Only draw on the left side
    stroke(0); // Black color for drawing
    strokeWeight(10); // Line thickness is set to 10
    line(pmouseX, pmouseY, mouseX, mouseY); // Draw a line following the mouse

    // Save the drawing points
    drawing.push({x: mouseX, y: mouseY});
  }
}

// Detect when the mouse is released
function mouseReleased() {
  // Generate a new Perlin noise grid on the middle section (R)
  dotGridR();

  // Generate the translation of the noise back into the sketch on the right side (P)
  f();

  // Regenerate the Perlin noise grid on board (A)
  dotGridA();

  // Translate noise from board A to board B
  translateAToB();
}

// Detect double-click to reset the left-side drawing board (L)
function mousePressed() {
  let currentTime = millis();
  if (currentTime - lastClickTime < doubleClickThreshold && mouseX <= sectionSize && mouseY <= sectionSize) {
    resetLeftSide();
  }
  lastClickTime = currentTime;
}

// Function to draw the grid of dots based on Perlin noise on the middle side (R)
function dotGridR() {
  noStroke();  // No border around circles
  fill(0);  // Set circle fill color to black

  // Clear the middle side by filling it with white before generating a new noise pattern
  fill(255);
  rect(sectionSize, 0, sectionSize, sectionSize);  // Clear middle side (R) by filling it with white
  fill(0);  // Reset fill to black for drawing circles

  // Randomize the noise offset for board R to generate a new pattern
  offsetR = random(1000);  // Change the noise offset to generate different noise patterns

  // Loop through x and y coordinates in increments set by the gap
  for (let x = sectionSize + gap / 2; x < sectionSize * 2; x += gap) {  // Start at x = sectionSize for the middle side
    for (let y = gap / 2; y < sectionSize; y += gap) {  // Loop in the middle region
      // Calculate Perlin noise value using scaled and offset coordinates
      let noiseValue = noise((x + offsetR) * xScale, (y + offsetR) * yScale);

      // Map noise value (0-1) to circle diameter between 0 and gap size
      let diameter = noiseValue * gap;
      circle(x, y, diameter);  // Draw a circle at (x, y) with calculated diameter
    }
  }
}

// Function to generate Perlin noise grid on board (A)
function dotGridA() {
  noStroke();  // No border around circles
  fill(0);  // Set circle fill color to black

  // Clear the bottom-right side (A) by filling it with white before generating a new noise pattern
  fill(255);
  rect(sectionSize, sectionSize, sectionSize, sectionSize);  // Clear the "A" section
  fill(0);  // Reset fill to black for drawing circles

  // Randomize the noise offset for board A to generate a different pattern from R
  offsetA = random(1000);  // Change the noise offset to generate different noise patterns

  // Loop through x and y coordinates in increments set by the gap
  for (let x = sectionSize + gap / 2; x < sectionSize * 2; x += gap) {  // Start at x = sectionSize for the bottom-right side (A)
    for (let y = sectionSize + gap / 2; y < sectionSize * 2; y += gap) {  // Loop in the bottom-right region
      // Calculate Perlin noise value using scaled and offset coordinates
      let noiseValue = noise((x + offsetA) * xScale, (y + offsetA) * yScale);

      // Map noise value (0-1) to circle diameter between 0 and gap size
      let diameter = noiseValue * gap;
      circle(x, y, diameter);  // Draw a circle at (x, y) with calculated diameter
    }
  }
}

// Function to translate Perlin noise from board A to board B
function translateAToB() {
  // Clear board B by filling it with white
  fill(255);
  rect(0, sectionSize * 2, sectionSize, sectionSize);  // Clear board B below A

  // Iterate through the points in board A and translate them to B
  let prevX, prevY;  // Variables to hold the previous point coordinates

  for (let x = sectionSize + gap / 2; x < sectionSize * 2; x += gap) {
    for (let y = sectionSize + gap / 2; y < sectionSize * 2; y += gap) {
      let noiseValue = noise((x + offsetA) * xScale, (y + offsetA) * yScale);
      let newX = x + map(noiseValue, 0, 1, -10, 10);  // Slightly distort x-coordinate
      let newY = y + map(noiseValue, 0, 1, -10, 10);  // Slightly distort y-coordinate

      // If there's a previous point, connect the dots
      if (prevX && prevY) {
        stroke(0);
        strokeWeight(10);  // Set line thickness to 10 for the preview in B
        line(prevX - sectionSize, prevY + sectionSize, newX - sectionSize, newY + sectionSize);  // Draw line connecting points in board B
      }

      prevX = newX;
      prevY = newY;
    }
  }
}

// Function f: translate sketch to Perlin noise and preview on the right side (P)
function f() {
  // Clear the preview side (P) by filling it with white
  fill(255);
  rect(0, sectionSize, sectionSize, sectionSize);  // Clear the preview side (P) by filling it with white (below L)
  fill(0);  // Reset fill to black for drawing points

  // Iterate through the drawing points on the left side
  let prevX, prevY;  // Variables to hold the previous point coordinates

  for (let i = 0; i < drawing.length; i++) {
    let pt = drawing[i];

    // Generate Perlin noise based on the point's coordinates
    let noiseValue = noise((pt.x + offsetR) * xScale, (pt.y + offsetR) * yScale);

    // Modify the x and y coordinates based on the noise value
    let newX = pt.x + map(noiseValue, 0, 1, -10, 10);  // Slightly distort x-coordinate
    let newY = pt.y + map(noiseValue, 0, 1, -10, 10);  // Slightly distort y-coordinate

    // If it's not the first point, connect the current point to the previous point
    if (i > 0) {
      stroke(0);
      strokeWeight(10);  // Set line thickness to 10 for the preview
      line(prevX, prevY + sectionSize, newX, newY + sectionSize);  // Draw line connecting points in the preview side (P) below L
    }

    // Update the previous point coordinates
    prevX = newX;
    prevY = newY;
  }
}

// Function to draw borders and labels with white background behind the text
function drawBoard() {
  stroke(0); // Set border color to black
  strokeWeight(2); // Set border thickness
  noFill();  // Do not fill the rectangles
  
  

  // Left side (Input space)
  rect(0, 0, sectionSize, sectionSize); // Draw the left border
  fill(255);  // White background for the text
  rect(textPadding, textPadding, rectPadding, rectPadding); // Draw a white rectangle behind the text
  fill(0); // Set fill to black for text
  textSize(labelSize); // Set text size
  text("L", textPadding * 2, textPadding * 4); // Label for left side

  // Middle side (Noise space)
  noFill();
  rect(sectionSize, 0, sectionSize, sectionSize); // Draw the middle border
  fill(255);  // White background for the text
  rect(sectionSize + textPadding, textPadding, rectPadding, rectPadding); // Draw a white rectangle behind the text
  fill(0); // Set fill to black for text
  textSize(labelSize); // Set text size
  text("R", sectionSize + textPadding * 2, textPadding * 4); // Label for middle side

  // Right side (Preview space below Left)
  noFill();
  rect(0, sectionSize, sectionSize, sectionSize); // Draw the right border for P
  fill(255);  // White background for the text
  rect(textPadding, sectionSize + textPadding, rectPadding, rectPadding); // Draw a white rectangle behind the text
  fill(0); // Set fill to black for text
  textSize(labelSize); // Set text size
  text("P", textPadding * 2, sectionSize + textPadding * 4); // Label for preview side (P)

  // New section for Perlin noise (A)
  noFill();
  rect(sectionSize, sectionSize, sectionSize, sectionSize); // Draw the bottom-right border for Perlin noise (A)
  fill(255);  // White background for the text
  rect(sectionSize + textPadding, sectionSize + textPadding, rectPadding, rectPadding); // Draw a white rectangle behind the text
  fill(0); // Set fill to black for text
  textSize(labelSize); // Set text size
  text("A", sectionSize + textPadding * 2, sectionSize + textPadding * 4); // Label for Perlin noise section (A)

  // New section for translated noise from A (B)
  noFill();
  rect(0, sectionSize * 2, sectionSize, sectionSize); // Draw the bottom-left border for translated noise (B)
  fill(255);  // White background for the text
  rect(textPadding, sectionSize * 2 + textPadding, rectPadding, rectPadding); // Draw a white rectangle behind the text
  fill(0); // Set fill to black for text
  textSize(labelSize); // Set text size
  text("B", textPadding * 2, sectionSize * 2 + textPadding * 4); // Label for translated Perlin noise section (B)
}

// Function to clear the left side (optional, for resetting)
function resetLeftSide() {
  noStroke();
  fill(255); // Fill the left side with white to "clear" it
  rect(0, 0, sectionSize, sectionSize); // Only clear the left side

  // Redraw the border and the "L" label
  drawBoard();

  // Clear the drawing array
  drawing = [];
}
