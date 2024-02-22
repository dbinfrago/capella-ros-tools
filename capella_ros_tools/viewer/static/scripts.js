/*
 * Copyright DB InfraGO AG and contributors
 * SPDX-License-Identifier: Apache-2.0
 */

import * as d3 from "https://cdn.jsdelivr.net/npm/d3@7/+esm";

export function initializeDiagram() {
    // Select the SVG container
    const svg = d3.select(".ClassDiagramBlank");
    svg.attr("width", "100%").attr("height", "100%");

    // Create a new group element
    const svgContainer = svg.append("g");

    svgContainer.attr("id", "svgContainer");

    // Select all children of the SVG container except the new group
    const children = svg.selectAll(":scope > *:not(#svgContainer)");

    // Move all children into the group
    children.each(function () {
        svgContainer.node().appendChild(this);
    });

    svgContainer.select("rect").remove();

    function escapeUUIDForCSSSelector(uuid) {
        // Escape first character if it's a digit
        let escapedUUID = uuid[0].match(/^\d/)
            ? "\\3" + uuid[0] + " " + uuid.slice(1)
            : uuid;
        // Escape hyphens
        return escapedUUID.replace(/-/g, "\\-");
    }

    let groupedNodes = [];

    svgContainer.selectAll(".Box").each(function () {
        if (groupedNodes.includes(this.id)) {
            return;
        }
        groupedNodes.push(this.id);

        var contextGroup = svgContainer.append("g");
        contextGroup.attr("class", "contextGroup");
        this.classList.forEach((id) => {
            let uuid = id.replace("context-", "");
            if (id == uuid) {
                // Not a context class
                return;
            }
            groupedNodes.push(uuid);
            let escapedUUID = escapeUUIDForCSSSelector(uuid);
            contextGroup
                .node()
                .appendChild(d3.select("#" + escapedUUID).node());
        });
    });

    const draggableElements = svgContainer.selectAll(".contextGroup");

    // Zoom and pan
    svg.call(
        d3.zoom().on("zoom", (event) => {
            svgContainer.attr("transform", event.transform);
        })
    );

    // Create an array of data with the same length as your selection
    let data = Array.from(draggableElements.nodes(), () => ({
        currentX: 0,
        currentY: 0,
        deltaX: 0,
        deltaY: 0,
    }));

    // Bind the data to your elements
    draggableElements.data(data);

    // Apply the drag behavior to the selected elements
    draggableElements.call(
        d3
            .drag()
            .on("start", dragStarted)
            .on("drag", dragged)
            .on("end", dragEnded)
    );

    function dragStarted(event, d) {
        // Implement any custom behavior on drag start if needed
        d.deltaX = event.x - d.currentX;
        d.deltaY = event.y - d.currentY;
    }

    function dragged(event, d) {
        // Implement any custom behavior on drag
        d.currentX = event.x - d.deltaX;
        d.currentY = event.y - d.deltaY;

        d3.select(this).attr(
            "transform",
            `translate(${d.currentX},${d.currentY})`
        );

        var boundingBox = svgContainer.node().getBBox();
        svgContainer
            .attr("width", boundingBox.width)
            .attr("height", boundingBox.height)
            .attr(
                "viewBox",
                `${boundingBox.x} ${boundingBox.y} ${boundingBox.width} ${boundingBox.height}`
            );
    }

    function dragEnded(event, d) {
        d.deltaX = event.x;
        d.deltaY = event.y;
    }
}

// Call initializeDiagram() when the DOM content is loaded
document.addEventListener("DOMContentLoaded", function () {
    initializeDiagram();
});
