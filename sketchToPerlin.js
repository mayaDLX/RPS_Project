// Noise scale variables for controlling the smoothness of the noise pattern
let xScale = 0.015;
let yScale = 0.02;

// Variables to control the gap and offset for Perlin noise
let gap = 20;  // Distance between circles in the grid
let offset = 100;  // Offset to shift the noise pattern

let drawing = [];  // Array to store the points from the sketch on the left side

function setup() {
  createCanvas(1536, 512);  // Split the canvas into three: 512x512 for each section
  background(255);  // Set background to white

  // Draw the borders and labels
  drawBoard();
  
  // Initial Perlin noise grid on the middle side (R)
  dotGrid();
}

function draw() {
  // Draw on the left side ("L") while holding the mouse
  if (mouseIsPressed && mouseX <= 512) {  // Only draw on the left side
    stroke(0); // Black color for drawing
    strokeWeight(2); // Line thickness
    line(pmouseX, pmouseY, mouseX, mouseY); // Draw a line following the mouse

    // Save the drawing points
    drawing.push({x: mouseX, y: mouseY});
  }
}

// Detect when the mouse is released
function mouseReleased() {
  // Generate a new Perlin noise grid on the middle section (R)
  dotGrid();

  // Generate the translation of the noise back into the sketch on the right side (P)
  f();
}

// Function to draw the grid of dots based on Perlin noise on the middle side (R)
function dotGrid() {
  noStroke();  // No border around circles
  fill(0);  // Set circle fill color to black

  // Clear the middle side by filling it with white before generating a new noise pattern
  fill(255);
  rect(512, 0, 512, 512);  // Clear middle side (R) by filling it with white
  fill(0);  // Reset fill to black for drawing circles

  // Randomize the noise offset to generate a new pattern each time
  offset = random(1000);  // Change the noise offset to generate different noise patterns

  // Loop through x and y coordinates in increments set by the gap
  for (let x = 512 + gap / 2; x < 1024; x += gap) {  // Start at x = 512 for the middle side
    for (let y = gap / 2; y < height; y += gap) {
      // Calculate noise value using scaled and offset coordinates
      let noiseValue = noise((x + offset) * xScale, (y + offset) * yScale);

      // Map noise value (0-1) to circle diameter between 0 and gap size
      let diameter = noiseValue * gap;
      circle(x, y, diameter);  // Draw a circle at (x, y) with calculated diameter
    }
  }
}

// Function f: translate sketch to Perlin noise and preview on the right side (P)
function f() {
  // Clear the preview side by filling it with white
  fill(255);
  rect(1024, 0, 512, 512);  // Clear the preview side (P) by filling it with white
  fill(0);  // Reset fill to black for drawing points

  // Iterate through the drawing points on the left side
  let prevX, prevY;  // Variables to hold the previous point coordinates

  for (let i = 0; i < drawing.length; i++) {
    let pt = drawing[i];

    // Generate Perlin noise based on the point's coordinates
    let noiseValue = noise((pt.x + offset) * xScale, (pt.y + offset) * yScale);

    // Modify the x and y coordinates based on the noise value
    let newX = pt.x + map(noiseValue, 0, 1, -10, 10);  // Slightly distort x-coordinate
    let newY = pt.y + map(noiseValue, 0, 1, -10, 10);  // Slightly distort y-coordinate

    // If it's not the first point, connect the current point to the previous point
    if (i > 0) {
      stroke(0);
      strokeWeight(2);
      line(prevX + 1024, prevY, newX + 1024, newY);  // Draw line connecting points in the preview side (P)
    }

    // Update the previous point coordinates
    prevX = newX;
    prevY = newY;
  }
}

// Function to draw borders and labels
function drawBoard() {
  stroke(0); // Set border color to black
  strokeWeight(2); // Set border thickness
  noFill();  // Do not fill the rectangles

  // Left side (Input space)
  rect(0, 0, 512, 512); // Draw the left border
  fill(0); // Set fill to black for text
  textSize(32); // Set text size
  text("L", 20, 50); // Label for left side

  // Middle side (Noise space)
  noFill();
  rect(512, 0, 512, 512); // Draw the middle border
  fill(0); // Set fill to black for text
  textSize(32); // Set text size
  text("R", 532, 50); // Label for middle side

  // Right side (Preview space)
  noFill();
  rect(1024, 0, 512, 512); // Draw the right border
  fill(0); // Set fill to black for text
  textSize(32); // Set text size
  text("P", 1044, 50); // Label for right side
}

// Function to clear the left side (optional, for resetting)
function resetLeftSide() {
  noStroke();
  fill(255); // Fill the left side with white to "clear" it
  rect(0, 0, 512, 512); // Only clear the left side

  // Redraw the border and the "L" label
  drawBoard();

  // Clear the drawing array
  drawing = [];
}
