// =====================================================================
// STALE REFERENCE ONLY - do not build from this file. 2026-09-06.
//
// Superseded twice:
//   D-010 - TP4056 removed and the external USB-C slot deleted. This file
//           still models both (TP4056_X/Y standoffs, USB_X_POS slot).
//   D-011 - enclosure CAD moved to Fusion 360 via the fusion-design skill.
//           OpenSCAD is no longer the workflow.
//
// Known geometry defects, independent of the decisions above:
//   - mixed centre-origin and corner-origin coordinates
//   - BROOK_HOLE_SPACING = 90 cannot fit a 52 mm board dimension
//   - a ventilation slot that falls outside the body
//   - foot recesses that subtract from nothing
//
// The parameter block below is still useful as dimensional reference.
// Authoritative numbers: docs/06-enclosure-reference.md
// =====================================================================

// Wireless Arcade Lap Pad Enclosure
// Two-piece snap-fit design for 3D printing
// OpenSCAD parametric design

// ====================
// PARAMETERS & CONFIG
// ====================

// View mode: "top", "bottom", "assembled"
VIEW_MODE = "assembled";

// Overall dimensions
PAD_WIDTH = 300;          // mm, overall width (left-right)
PAD_DEPTH = 200;          // mm, overall depth (front-back)
PAD_HEIGHT = 40;          // mm, overall height
CORNER_RADIUS = 10;       // mm, rounded corner radius

// Top plate
TOP_THICKNESS = 3;        // mm
BUTTON_HOLE_DIA = 30;     // mm, action button hole diameter
JOYSTICK_HOLE_DIA = 24;   // mm, Sanwa JLF center hole

// Bottom tray
BOTTOM_DEPTH = 35;        // mm, internal depth for electronics
WALL_THICKNESS = 2;       // mm, minimum wall thickness

// Snap-fit tabs
SNAP_TAB_WIDTH = 15;      // mm, width of each snap-fit tab
SNAP_TAB_DEPTH = 5;       // mm, depth (how far they protrude)
SNAP_TAB_HEIGHT = 2;      // mm, vertical thickness of tabs
SNAP_TAB_SPACING = 60;    // mm, spacing between tabs from center

// Standoff dimensions
STANDOFF_HEIGHT = 8;      // mm, height above bottom
STANDOFF_DIA = 6;         // mm, diameter for M3 screws
STANDOFF_WALL = 1.5;      // mm, wall thickness for standoffs

// Component dimensions and positions
// Brook Gen 5W: 97mm x 52mm, 4 corner M3 holes
BROOK_WIDTH = 97;
BROOK_DEPTH = 52;
BROOK_X = 100;            // mm from left edge
BROOK_Y = 60;             // mm from front edge
BROOK_HOLE_SPACING = 90;  // mm, diagonal spacing

// TP4056 charging module: 26mm x 17mm
TP4056_WIDTH = 26;
TP4056_DEPTH = 17;
TP4056_X = 220;
TP4056_Y = 80;

// LiPo battery: 95mm x 33mm x 10mm
BATTERY_WIDTH = 95;
BATTERY_DEPTH = 33;
BATTERY_HEIGHT = 10;
BATTERY_X = 105;
BATTERY_Y = 30;

// Qi receiver coil
QI_DIA = 50;              // mm, diameter of coil
QI_DEPTH = 1.5;           // mm, recess depth

// USB-C access
USB_WIDTH = 12;           // mm, slot width
USB_HEIGHT = 8;           // mm, slot height
USB_X_POS = 145;          // mm, position on bottom edge

// Anti-slip feet
FOOT_DIA = 10;            // mm, diameter of foot recess
FOOT_DEPTH = 1.5;         // mm, depth of recess
FOOT_INSET = 15;          // mm, inset from corner

// Text label
LABEL_TEXT = "PLAYER 1";
TEXT_SIZE = 8;            // mm, font size

// Joystick position (left third of pad)
STICK_X = 80;             // mm from left edge
STICK_Y = 100;            // mm from front edge

// Button cluster positions (right of joystick)
BTN_START_X = 170;        // mm, left button of top row
BTN_START_Y = 70;         // mm, top row Y position
BTN_SPACING_X = 36;       // mm, center-to-center horizontal spacing
BTN_SPACING_Y = 30;       // mm, row-to-row vertical spacing
BTN_ROW_OFFSET_X = 12;    // mm, offset for second row

// OLED display cutout: 27mm x 15mm
OLED_WIDTH = 27;
OLED_HEIGHT = 15;
OLED_X = 150;             // mm from left edge
OLED_Y = 170;             // mm from front edge (near top)

// Ventilation
VENT_SLOT_WIDTH = 4;      // mm, width of ventilation slots
VENT_SLOT_DEPTH = 60;     // mm, length of ventilation slots
VENT_SPACING = 10;        // mm, spacing between slots

// Cable routing
CABLE_CHANNEL_WIDTH = 5;  // mm
CABLE_CHANNEL_DEPTH = 2;  // mm

// Tolerance
TOLERANCE = 0.3;          // mm, snap-fit tolerance


// ====================
// MODULES & FUNCTIONS
// ====================

// Rounded rectangle (2D)
module rounded_rect_2d(width, depth, radius) {
    offset(r = radius) {
        offset(r = -radius) {
            square([width, depth], center = true);
        }
    }
}

// Rounded rectangle (3D extrusion)
module rounded_rect(width, depth, height, radius) {
    linear_extrude(height = height) {
        rounded_rect_2d(width, depth, radius);
    }
}

// Snap-fit tab (protrudes from edge)
module snap_tab(tab_width, tab_depth, tab_height) {
    cube([tab_width, tab_depth, tab_height], center = true);
}

// Rounded cylinder for buttons/joystick holes
module button_hole(diameter, depth = 5) {
    cylinder(d = diameter, h = depth, $fn = 40);
}

// Standoff for component mounting
module standoff(height, dia, wall_thickness) {
    difference() {
        cylinder(h = height, d = dia + wall_thickness * 2, $fn = 20);
        cylinder(h = height, d = dia, $fn = 20);
    }
}

// Anti-slip foot recess
module foot_recess(dia, depth, inset) {
    translate([inset, inset, 0]) {
        cylinder(h = depth, d = dia, $fn = 20);
    }
}


// ====================
// TOP PLATE
// ====================

module top_plate() {
    difference() {
        // Main top plate body
        rounded_rect(PAD_WIDTH, PAD_DEPTH, TOP_THICKNESS, CORNER_RADIUS);

        // ===== JOYSTICK CUTOUTS =====
        translate([STICK_X, STICK_Y, -0.5]) {
            // Center hole for joystick shaft
            cylinder(d = JOYSTICK_HOLE_DIA, h = TOP_THICKNESS + 1, $fn = 40);

            // Sanwa JLF mounting holes (4 corner holes on ~84mm diagonal)
            // Standard pattern: holes on 40mm centers forming square
            hole_spacing = 40;
            for (dx = [-hole_spacing/2, hole_spacing/2]) {
                for (dy = [-hole_spacing/2, hole_spacing/2]) {
                    translate([dx, dy, 0]) {
                        cylinder(d = 4.2, h = TOP_THICKNESS + 1, $fn = 20);
                    }
                }
            }
        }

        // ===== ACTION BUTTON CUTOUTS =====
        // 6 buttons in 2x3 layout (Vewlix-style)
        // Top row: 3 buttons
        for (i = [0:2]) {
            btn_x = BTN_START_X + i * BTN_SPACING_X;
            btn_y = BTN_START_Y;
            translate([btn_x, btn_y, -0.5]) {
                button_hole(BUTTON_HOLE_DIA, TOP_THICKNESS + 1);
            }
        }

        // Bottom row: 3 buttons (offset)
        for (i = [0:2]) {
            btn_x = BTN_START_X + BTN_ROW_OFFSET_X + i * BTN_SPACING_X;
            btn_y = BTN_START_Y + BTN_SPACING_Y;
            translate([btn_x, btn_y, -0.5]) {
                button_hole(BUTTON_HOLE_DIA, TOP_THICKNESS + 1);
            }
        }

        // ===== OLED DISPLAY CUTOUT =====
        translate([OLED_X, OLED_Y, -0.5]) {
            cube([OLED_WIDTH, OLED_HEIGHT, TOP_THICKNESS + 1], center = true);
        }
    }

    // ===== SNAP-FIT TABS (on underside of top plate) =====
    // Front edge tabs
    for (x_offset = [-SNAP_TAB_SPACING, 0, SNAP_TAB_SPACING]) {
        translate([x_offset, -PAD_DEPTH/2 + SNAP_TAB_DEPTH/2, -SNAP_TAB_HEIGHT]) {
            snap_tab(SNAP_TAB_WIDTH, SNAP_TAB_DEPTH, SNAP_TAB_HEIGHT);
        }
    }

    // Back edge tabs
    for (x_offset = [-SNAP_TAB_SPACING, 0, SNAP_TAB_SPACING]) {
        translate([x_offset, PAD_DEPTH/2 - SNAP_TAB_DEPTH/2, -SNAP_TAB_HEIGHT]) {
            snap_tab(SNAP_TAB_WIDTH, SNAP_TAB_DEPTH, SNAP_TAB_HEIGHT);
        }
    }

    // Left edge tabs
    for (y_offset = [-SNAP_TAB_SPACING, 0, SNAP_TAB_SPACING]) {
        translate([-PAD_WIDTH/2 + SNAP_TAB_DEPTH/2, y_offset, -SNAP_TAB_HEIGHT]) {
            snap_tab(SNAP_TAB_DEPTH, SNAP_TAB_WIDTH, SNAP_TAB_HEIGHT);
        }
    }

    // Right edge tabs
    for (y_offset = [-SNAP_TAB_SPACING, 0, SNAP_TAB_SPACING]) {
        translate([PAD_WIDTH/2 - SNAP_TAB_DEPTH/2, y_offset, -SNAP_TAB_HEIGHT]) {
            snap_tab(SNAP_TAB_DEPTH, SNAP_TAB_WIDTH, SNAP_TAB_HEIGHT);
        }
    }
}


// ====================
// BOTTOM TRAY
// ====================

module bottom_tray() {
    difference() {
        union() {
            // Main tray body (box)
            linear_extrude(height = BOTTOM_DEPTH) {
                rounded_rect_2d(PAD_WIDTH, PAD_DEPTH, CORNER_RADIUS);
            }

            // ===== COMPONENT STANDOFFS =====

            // Brook Gen 5W board: 4 corner standoffs
            brook_holes = [
                [BROOK_X - BROOK_HOLE_SPACING/2, BROOK_Y - BROOK_HOLE_SPACING/2],
                [BROOK_X + BROOK_HOLE_SPACING/2, BROOK_Y - BROOK_HOLE_SPACING/2],
                [BROOK_X - BROOK_HOLE_SPACING/2, BROOK_Y + BROOK_HOLE_SPACING/2],
                [BROOK_X + BROOK_HOLE_SPACING/2, BROOK_Y + BROOK_HOLE_SPACING/2]
            ];

            for (pos = brook_holes) {
                translate([pos[0], pos[1], 0]) {
                    standoff(STANDOFF_HEIGHT, STANDOFF_DIA, STANDOFF_WALL);
                }
            }

            // TP4056 module: 2 corner standoffs
            tp4056_holes = [
                [TP4056_X - TP4056_WIDTH/2 + 3, TP4056_Y - TP4056_DEPTH/2 + 3],
                [TP4056_X + TP4056_WIDTH/2 - 3, TP4056_Y + TP4056_DEPTH/2 - 3]
            ];

            for (pos = tp4056_holes) {
                translate([pos[0], pos[1], 0]) {
                    standoff(STANDOFF_HEIGHT * 0.6, STANDOFF_DIA, STANDOFF_WALL);
                }
            }
        }

        // ===== QI RECEIVER COIL RECESS (bottom flush) =====
        translate([PAD_WIDTH/2 - 40, PAD_DEPTH/2 - 30, BOTTOM_DEPTH - QI_DEPTH]) {
            cylinder(d = QI_DIA, h = QI_DEPTH + 0.5, $fn = 40);
        }

        // ===== USB-C ACCESS SLOT =====
        translate([USB_X_POS, -PAD_DEPTH/2, BOTTOM_DEPTH/2 - USB_HEIGHT/2]) {
            cube([USB_WIDTH, WALL_THICKNESS + 1, USB_HEIGHT], center = true);
        }

        // ===== VENTILATION SLOTS (sides) =====
        // Left side slots
        for (i = [0:3]) {
            slot_y = -PAD_DEPTH/4 + i * (VENT_SPACING + VENT_SLOT_DEPTH);
            translate([-PAD_WIDTH/2 + WALL_THICKNESS/2, slot_y, BOTTOM_DEPTH/2]) {
                cube([WALL_THICKNESS + 0.5, VENT_SLOT_DEPTH, VENT_SLOT_WIDTH], center = true);
            }
        }

        // Right side slots
        for (i = [0:3]) {
            slot_y = -PAD_DEPTH/4 + i * (VENT_SPACING + VENT_SLOT_DEPTH);
            translate([PAD_WIDTH/2 - WALL_THICKNESS/2, slot_y, BOTTOM_DEPTH/2]) {
                cube([WALL_THICKNESS + 0.5, VENT_SLOT_DEPTH, VENT_SLOT_WIDTH], center = true);
            }
        }

        // ===== CABLE ROUTING CHANNELS =====
        // Channel from Brook to TP4056
        translate([(BROOK_X + TP4056_X)/2, (BROOK_Y + TP4056_Y)/2, CABLE_CHANNEL_DEPTH/2]) {
            cube([CABLE_CHANNEL_WIDTH, 40, CABLE_CHANNEL_DEPTH], center = true);
        }

        // Channel to battery bay
        translate([(BROOK_X + BATTERY_X)/2, (BROOK_Y + BATTERY_Y)/2, CABLE_CHANNEL_DEPTH/2]) {
            cube([CABLE_CHANNEL_WIDTH, 40, CABLE_CHANNEL_DEPTH], center = true);
        }
    }

    // ===== SNAP-FIT RECEPTACLES (on rim of tray) =====
    // Front receptacles
    for (x_offset = [-SNAP_TAB_SPACING, 0, SNAP_TAB_SPACING]) {
        translate([x_offset, -PAD_DEPTH/2 + SNAP_TAB_DEPTH/2, BOTTOM_DEPTH - SNAP_TAB_HEIGHT]) {
            snap_tab(SNAP_TAB_WIDTH, SNAP_TAB_DEPTH, SNAP_TAB_HEIGHT);
        }
    }

    // Back receptacles
    for (x_offset = [-SNAP_TAB_SPACING, 0, SNAP_TAB_SPACING]) {
        translate([x_offset, PAD_DEPTH/2 - SNAP_TAB_DEPTH/2, BOTTOM_DEPTH - SNAP_TAB_HEIGHT]) {
            snap_tab(SNAP_TAB_WIDTH, SNAP_TAB_DEPTH, SNAP_TAB_HEIGHT);
        }
    }

    // Left receptacles
    for (y_offset = [-SNAP_TAB_SPACING, 0, SNAP_TAB_SPACING]) {
        translate([-PAD_WIDTH/2 + SNAP_TAB_DEPTH/2, y_offset, BOTTOM_DEPTH - SNAP_TAB_HEIGHT]) {
            snap_tab(SNAP_TAB_DEPTH, SNAP_TAB_WIDTH, SNAP_TAB_HEIGHT);
        }
    }

    // Right receptacles
    for (y_offset = [-SNAP_TAB_SPACING, 0, SNAP_TAB_SPACING]) {
        translate([PAD_WIDTH/2 - SNAP_TAB_DEPTH/2, y_offset, BOTTOM_DEPTH - SNAP_TAB_HEIGHT]) {
            snap_tab(SNAP_TAB_DEPTH, SNAP_TAB_WIDTH, SNAP_TAB_HEIGHT);
        }
    }

    // ===== ANTI-SLIP FOOT RECESSES (on bottom outer surface) =====
    difference() {
        union() {}

        // Front-left foot
        translate([-PAD_WIDTH/2, -PAD_DEPTH/2, -0.1]) {
            foot_recess(FOOT_DIA, FOOT_DEPTH, FOOT_INSET);
        }

        // Front-right foot
        translate([PAD_WIDTH/2, -PAD_DEPTH/2, -0.1]) {
            translate([-FOOT_INSET, 0, 0]) {
                foot_recess(FOOT_DIA, FOOT_DEPTH, 0);
            }
        }

        // Back-left foot
        translate([-PAD_WIDTH/2, PAD_DEPTH/2, -0.1]) {
            translate([0, -FOOT_INSET, 0]) {
                foot_recess(FOOT_DIA, FOOT_DEPTH, 0);
            }
        }

        // Back-right foot
        translate([PAD_WIDTH/2, PAD_DEPTH/2, -0.1]) {
            translate([-FOOT_INSET, -FOOT_INSET, 0]) {
                foot_recess(FOOT_DIA, FOOT_DEPTH, 0);
            }
        }
    }

    // ===== EMBOSSED TEXT LABEL =====
    translate([-PAD_WIDTH/2 + 40, PAD_DEPTH/2 - 25, BOTTOM_DEPTH - 0.5]) {
        linear_extrude(height = 0.8) {
            text(LABEL_TEXT, size = TEXT_SIZE, halign = "left", valign = "center",
                 font = "Arial:style=Bold");
        }
    }
}


// ====================
// ASSEMBLY & VISUALIZATION
// ====================

module assembled_view() {
    // Bottom tray at z=0
    bottom_tray();

    // Top plate positioned above
    translate([0, 0, BOTTOM_DEPTH]) {
        top_plate();
    }

    // Optional: Show component outlines for reference (commented out)
    // %translate([BROOK_X, BROOK_Y, 1]) {
    //     cube([BROOK_WIDTH, BROOK_DEPTH, 5], center = true);
    // }
}


// ====================
// MAIN RENDER
// ====================

if (VIEW_MODE == "top") {
    top_plate();
} else if (VIEW_MODE == "bottom") {
    bottom_tray();
} else if (VIEW_MODE == "assembled") {
    assembled_view();
} else {
    // Default to assembled
    assembled_view();
}

// Recommended print settings:
// - PLA or PETG
// - 0.2mm layer height
// - 100% infill for structural parts, 15-20% for tray walls
// - Print top plate flat (no supports needed)
// - Print bottom tray flat (no supports needed if coil recess is on top during print)
// - Snap-fit tolerance: 0.3mm allows easy insertion while maintaining grip
