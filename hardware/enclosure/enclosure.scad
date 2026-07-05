include <./YAPPgenerator_v3.scad>

pcbLength = 40;
pcbWidth = 60;
pcbThickness = 1.6;

// paddingFront = 1.5;
// paddingBack = 1.5;
// paddingRight = 2.5;
// paddingLeft = 2.5;

// ridgeHeight = 6;
lidWallHeight  = 13;
baseWallHeight = 6;
wallThickness = 2;

standoffHeight = 6;
standoffDiameter = 4.5;
standoffPinDiameter = 1.94;
standoffHoleSlack = 0.6;

// * Print settings *
// printLidShell = false;
// printBaseShell = false;

// * Debug settings *
// showPCB = true;
// hideLidWalls = true;
// showSideBySide = false;
// onLidGap = 6;

// snapJoins = [
//     [6, 6, yappLeft, yappRight],
//     [pcbLength+paddingRight+paddingLeft-6, 6, yappLeft, yappRight]
// ];

pcbStands = [
    [2.5, 2.5, standoffHeight, yappDefault, standoffDiameter, standoffPinDiameter, standoffHoleSlack, 0, yappBoth, yappPin, yappAllCorners, yappCoordPCB]
];

// hole for usb-c connector
cutoutsLeft = [
    [
      ((pcbLength-13)/2) + 2.54, // from Back
      3, // from Left
      11, // width
      7, // length
      1, // radius
      yappRoundedRect, // shape
      0, // depth
      0, // angle
      // yappCenter,
      yappCoordPCB,
    ]
];

// hole for the photodiode
cutoutsLid = [
    [5, 33, 13, 12, 6, yappRectangle]
];

// module hookLidInside()
// {
  // translate([20, 34, -5])
  //   cube([2, 12, 12]);

  // translate([20+14, 34, -5])
  //   cube([2, 12, 12]);

  // translate([20, 34-2, -5])
  //   cube([16, 2, 12]);

  // translate([20, 34+12, -5])
  //   cube([16, 2, 12]);
// }

// guides for the elastic band
module hookLidOutside()
{
  // back
  // base x value: -4
  translate([-6, 20, -12.5])
    cube([2, 10, 3]);

  translate([-6, 20, -12.5])
    cube([4, 2, 3]);

  translate([-6, 30, -12.5])
    cube([4, 2, 3]);

  // front
  // base x value: 44
  translate([46, 20, -12.5])
    cube([2, 10, 3]);

  translate([44, 20, -12.5])
    cube([4, 2, 3]);

  translate([44, 30, -12.5])
    cube([4, 2, 3]);
}

YAPPgenerate();