(function () {
    const tooltipStyles = `
      .market-value-tooltip {
        position: absolute;
        padding: 8px;
        background: rgba(0, 0, 0, 0.8);
        color: white;
        border-radius: 4px;
        font-size: 12px;
        pointer-events: none;
        z-index: 1000;
        visibility: hidden;
      }
    `;
    const styleSheet = document.createElement("style");
    styleSheet.innerText = tooltipStyles;
    document.head.appendChild(styleSheet);

    function createVisualization(playerData, marketData, colormap) {
        console.log("Received Player Data:", playerData);
        console.log("Received Market Data:", marketData);
        console.log("Received Colormap:", colormap);
    
        const container = d3.select("#d3-visualization-container");
    
        // Clear the container first
        container.selectAll("*").remove();

        // Normalize input data and ensure proper type-checking
        const validPlayerData = Array.isArray(playerData) ? playerData : [];
        const validMarketData = Array.isArray(marketData) ? marketData : [];
        const validColormap = colormap && typeof colormap === "object" && colormap.stops && Array.isArray(colormap.stops)
            ? colormap
            : { stops: [] };

        //console.log("Valid Player Data:", validPlayerData);
        //console.log("Valid Market Data:", validMarketData);
        //console.log("Valid Colormap:", validColormap);

        // Check if all datasets are empty
        const isEmptyData =
            validPlayerData.length === 0 &&
            validMarketData.length === 0 &&
            validColormap.stops.length === 0;

        //console.log("isEmptyData:", isEmptyData);

        if (isEmptyData) {
            // Show the "No valid lineup data selected" message
            container.append("div")
                .attr("class", "no-data-message")
                .style("text-align", "center")
                .style("font-size", "18px")
                .style("color", "red")
                .text("No valid lineup data selected");
            return;
        }
        
        const tooltip = d3.select("body")
            .append("div")
            .attr("class", "market-value-tooltip")
            .style("position", "absolute")
            .style("visibility", "hidden");
    
        let svg = container.select("svg");
        if (svg.empty()) {
            //console.log("Adding soccer field SVG.");
            svg = container.append("svg")
                .attr("width", 1400)
                .attr("height", 820);
    
            svg.append("rect")
                .attr("x", 50)
                .attr("y", 50)
                .attr("width", 500)
                .attr("height", 700)
                .attr("fill", "green")
                .attr("stroke", "white")
                .attr("stroke-width", 2);
    
            svg.append("circle")
                .attr("cx", 300)
                .attr("cy", 400)
                .attr("r", 50)
                .attr("fill", "none")
                .attr("stroke", "white")
                .attr("stroke-width", 2);
    
            svg.append("rect")
                .attr("x", 200)
                .attr("y", 50)
                .attr("width", 200)
                .attr("height", 100)
                .attr("fill", "none")
                .attr("stroke", "white")
                .attr("stroke-width", 2);
    
            svg.append("rect")
                .attr("x", 200)
                .attr("y", 650)
                .attr("width", 200)
                .attr("height", 100)
                .attr("fill", "none")
                .attr("stroke", "white")
                .attr("stroke-width", 2);
        }
    
        svg.selectAll(".legend").remove();
        createLegend(svg, colormap, 600, 50, 500, 20);

        const playerCircleRadius = 8; // radius of player circle
        const nameYOffset = -15; // vertical offset for player name
        const cardSize = 8; // size of the card square
        const cardSpacing = 2; // spacing between multiple cards
    
        // Add an info icon near the legend
        const legendWidth = 500; // Ensure this matches the actual legend width
        const infoGroup = svg.append("g")
            .attr("class", "info-icon")
            .attr("transform", `translate(${600 + legendWidth + 20}, 60)`); // Adjust position relative to legend
    
        // Create a circle for the info icon
        infoGroup.append("circle")
            .attr("r", 10) // Radius of the circle
            .attr("fill", "#555") // Dark gray color
            .attr("cx", 0)
            .attr("cy", 0);
    
        // Add "i" text inside the circle
        infoGroup.append("text")
            .attr("x", 0)
            .attr("y", 4) // Adjust to vertically center the text
            .attr("text-anchor", "middle")
            .attr("fill", "white")
            .attr("font-size", "12px")
            .attr("font-weight", "bold")
            .text("i");
    
        // Add hover tooltip for the info icon
        infoGroup.on("mouseover", function (event) {
            tooltip
                .style("visibility", "visible")
                .html(`
                    <strong>Information:</strong><br/>
                    This visualization displays player positions, market values, and<br/>
                    Average Match Outcome Points (AMOP). AMOP are calculated by <br/>
                    all the games a player participated in and the outcome of those games.<br/>
                    (A loss results in 0, a draw in 1 a victory in 3 points).<br/>
                    Goals and cards are also displayed if available. Please note <br/>
                    that players shooting goals that were not in the initial lineup will not be displayed.
                `);
        })
        .on("mousemove", function (event) {
            tooltip
                .style("top", `${event.pageY - 10}px`)
                .style("left", `${event.pageX + 10}px`);
        })
        .on("mouseout", function () {
            tooltip.style("visibility", "hidden");
        });

        svg.selectAll(".player-position").remove();
        svg.selectAll(".market-value-bar").remove();
        svg.selectAll(".market-value-text").remove();

        if (playerData && playerData.length > 0) {
            playerData.forEach(player => {
                if (player.x != null && player.y != null) {
                    const px = 300 + player.x * 50;
                    const py = 400 + player.y * 50;
    
                    // Draw player circle
                    svg.append("circle")
                        .attr("class", "player-position")
                        .attr("cx", px)
                        .attr("cy", py)
                        .attr("r", playerCircleRadius)
                        .attr("fill", "white")
                        .attr("stroke", "black")
                        .attr("stroke-width", 1);
    
                    // Draw player name
                    svg.append("text")
                        .attr("class", "player-position")
                        .attr("x", px)
                        .attr("y", py + nameYOffset)
                        .attr("text-anchor", "middle")
                        .attr("fill", "white")
                        .style("stroke", "black")
                        .style("stroke-width", "0.5px")
                        .style("paint-order", "stroke")
                        .text(formatPlayerName(player.name) || "Unknown");
                    
                    const eventSymbols = [];
                    // Cards
                    const cards = Array.isArray(player.cards) ? player.cards : [];
                    cards.forEach(card => {
                        const cardColor = (card === "red" ? "red" : "yellow");
                        eventSymbols.push({ type: "card", color: cardColor });
                    });

                    // Goals
                    const goals = Array.isArray(player.goals) ? player.goals : [];
                    goals.forEach(g => {
                        eventSymbols.push({ type: "goal" });
                    });

                    // Reafractored code placing event items next to each other to avoid overlap
                    const baseX = px + 20;
                    const baseY = py + nameYOffset; 
                    
                    eventSymbols.forEach((ev, index) => {
                        const offsetX = index * (cardSize + cardSpacing + 5); // +5 for goals a bit bigger than cards
                        
                        if (ev.type === "card") {
                            svg.append("rect")
                                .attr("class", "player-card")
                                .attr("x", baseX + offsetX)
                                .attr("y", baseY - cardSize + 15)
                                .attr("width", cardSize)
                                .attr("height", cardSize)
                                .attr("fill", ev.color)
                                .attr("stroke", "black")
                                .attr("stroke-width", 0.5);
                        } else if (ev.type === "goal") {
                            // Draw a small soccer ball symbol
                            const ballRadius = 6;
                            // We place the ball top right as well, slightly larger offset
                            const ballGroup = svg.append("g")
                                .attr("class", "goal-symbol")
                                .attr("transform", `translate(${baseX + offsetX}, ${baseY + 15})`);
                            
                            ballGroup.append("circle")
                                .attr("r", ballRadius)
                                .attr("fill", "white")
                                .attr("stroke", "black")
                                .attr("stroke-width", 1);

                            const hexPatterns = [
                                { dx: 0, dy: -ballRadius / 2 },
                                { dx: ballRadius / 2, dy: ballRadius / 4 },
                                { dx: -ballRadius / 2, dy: ballRadius / 4 },
                                { dx: ballRadius / 4, dy: ballRadius / 2 },
                                { dx: -ballRadius / 4, dy: ballRadius / 2 }
                            ];
                            hexPatterns.forEach(({ dx, dy }) => {
                                ballGroup.append("circle")
                                    .attr("cx", dx)
                                    .attr("cy", dy)
                                    .attr("r", ballRadius / 5)
                                    .attr("fill", "black");
                            });
                        }
                    });
                }
            });
        }

        if (marketData && marketData.length > 0) {
            const yGroups = {};
            marketData.forEach((bar) => {
                if (!yGroups[bar.y]) {
                    yGroups[bar.y] = [];
                }
                yGroups[bar.y].push(bar);
            });
            
            // Sort each group by x-coordinate (ascending)
            Object.keys(yGroups).forEach((y) => {
                yGroups[y] = yGroups[y].sort((a, b) => a.x - b.x);
            });

            Object.entries(yGroups).forEach(([y, group]) => {
                y = parseFloat(y);
                let offset = 12;

                if (group.length === 3) {
                    offset = 22; // With 3 players, we need more space between them
                }

                group.forEach((bar, index) => {
                    const n = group.length;
                    if (n === 1) {
                        bar.yAdjusted = 400 + y * 50;
                    } else if (n === 2) {
                        bar.yAdjusted = 400 + y * 50 + (index === 0 ? -offset : offset);
                    } else if (n === 3) {
                        bar.yAdjusted = 400 + y * 50 + (index - 1) * offset;
                    } else {
                        const relativePosition = index - (n - 1) / 2;
                        bar.yAdjusted = 400 + y * 50 + relativePosition * offset;
                    }
                });
            });

            const barX = 550;
            const marginRight = 70; // a margin, because otherwise the last x axis tick gets cut off
            const availableWidth = (1400 - barX) - marginRight;
            const maxMarketValue = Math.max(...marketData.map(bar => bar.market_value));

            marketData.forEach((bar) => {
                const barWidth = (bar.market_value / maxMarketValue) * availableWidth;
                const barHeight = 20;
                const fontSize = 14;

                svg.append("rect")
                    .attr("class", "market-value-bar")
                    .attr("x", barX)
                    .attr("y", bar.yAdjusted)
                    .attr("width", barWidth)
                    .attr("height", barHeight)
                    .attr("fill", bar.color)
                    .on("mouseover", function (event) {
                        tooltip
                            .style("visibility", "visible")
                            .html(`
                                <strong>${bar.name}</strong><br/>
                                Market Value: €${bar.market_value.toLocaleString()}<br/>
                                Position: ${bar.position || 'N/A'}<br/>
                                AMOP: ${(bar.gpa || 0).toFixed(2)}
                            `);
                    })
                    .on("mousemove", function (event) {
                        tooltip
                            .style("top", `${event.pageY - 10}px`)
                            .style("left", `${event.pageX + 10}px`);
                    })
                    .on("mouseout", function () {
                        tooltip.style("visibility", "hidden");
                    });

                const valueText = `${(bar.market_value / 1000000).toFixed(2)}M`;
                const valueTextWidth = valueText.length * fontSize * 0.6;
                const playerNameWidth = bar.name.length * fontSize * 0.6;

                const showValueTextInside = valueTextWidth <= barWidth - 10;
                const availableSpaceForName = showValueTextInside
                    ? barWidth - valueTextWidth - 10
                    : barWidth - 10;

                const showNameInside = playerNameWidth <= availableSpaceForName;

                const textColor = getContrastColor(bar.color);

                if (showNameInside) {
                    svg.append("text")
                        .attr("class", "market-value-text")
                        .attr("x", barX + 5)
                        .attr("y", bar.yAdjusted + barHeight / 2 + 5)
                        .attr("fill", textColor)
                        .attr("font-size", `${fontSize}px`)
                        .attr("text-anchor", "start")
                        .text(formatPlayerName(bar.name));
                }
                
                // here we don't use textColor because the text of the marketval could be either inside or outside the bar and outside it should always be black
                const marketValueTextColor = showValueTextInside
                    ? getContrastColor(bar.color) // Dynamically calculate color for inside text
                    : "black"; // Default to black for outside text

                svg.append("text")
                    .attr("class", "market-value-text")
                    .attr("x", showValueTextInside ? barX + barWidth - 5 : barX + barWidth + 10)
                    .attr("y", bar.yAdjusted + barHeight / 2 + 5)
                    .attr("fill",marketValueTextColor)
                    .attr("font-size", `${fontSize}px`)
                    .attr("text-anchor", showValueTextInside ? "end" : "start")
                    .text(valueText);
            });

            // Axis for Market Value
            const tickValues = [0, 0.25, 0.5, 0.75, 1].map(percent => maxMarketValue * percent);
            svg.append("line")
                .attr("class", "market-value-axis")
                .attr("x1", barX)
                .attr("y1", 750)
                .attr("x2", barX + availableWidth)
                .attr("y2", 750)
                .attr("stroke", "black")
                .attr("stroke-width", 1);

            tickValues.forEach(value => {
                const xPos = barX + (value / maxMarketValue) * availableWidth;
                svg.append("line")
                    .attr("class", "market-value-tick")
                    .attr("x1", xPos)
                    .attr("y1", 750)
                    .attr("x2", xPos)
                    .attr("y2", 755)
                    .attr("stroke", "black")
                    .attr("stroke-width", 1);

                svg.append("text")
                    .attr("class", "market-value-text")
                    .attr("x", xPos)
                    .attr("y", 770)
                    .attr("text-anchor", "middle")
                    .attr("font-size", "12px")
                    .text(`€${(value / 1000000).toFixed(1)}M`);
            });

            svg.append("text")
                .attr("class", "market-value-text")
                .attr("x", barX + availableWidth / 2)
                .attr("y", 790)
                .attr("text-anchor", "middle")
                .attr("font-size", "14px")
                .text("Market Value");
        }
    }

    function attachObservers() {
        const container = document.getElementById('d3-visualization-container');
        if (!container) {
            console.error("d3-visualization-container not found.");
            return;
        }

        const updateVisualization = () => {
            //console.log("Raw data-colormap attribute:", container.getAttribute("data-colormap"));
            
            const playerData = JSON.parse(container.getAttribute("data-player-data") || "[]");
            const marketData = JSON.parse(container.getAttribute("data-market-data") || "[]");
            const colormap = JSON.parse(container.getAttribute("data-colormap") || "{}");
            
            //console.log("Parsed colormap:", colormap);
            //console.log("Container attributes:", container.attributes);
            
            createVisualization(playerData, marketData, colormap);
        };

        new MutationObserver(updateVisualization).observe(container, {
            attributes: true,
            attributeFilter: ["data-player-data", "data-market-data", "data-colormap"]
        });

        createVisualization([], [], {});
        //console.log("Observer attached to d3-visualization-container.");
    }

    document.addEventListener("DOMContentLoaded", () => {
        const checkContainerInterval = setInterval(function () {
            const containerExists = document.getElementById('d3-visualization-container');
            if (containerExists) {
                attachObservers();
                clearInterval(checkContainerInterval);
            }
        }, 100);
    });
})();


function formatPlayerName(fullName) {
    if (!fullName) return "Unknown";
    const parts = fullName.split(" ");
    if (parts.length > 1) {
        return parts[0][0] + ". " + parts[parts.length - 1];
    }
    return fullName;
}

function createLegend(svg, legendData, x, y, width, height) {
    if (!legendData || !legendData.stops || legendData.stops.length === 0) {
        console.error("Legend data is missing or invalid!");
        return;
    }

    const { stops, min_gpa, max_gpa, dynamic_min, dynamic_max } = legendData;

    const legendGroup = svg.append("g")
        .attr("class", "legend")
        .attr("transform", `translate(${x}, ${y})`);

    const defs = legendGroup.append("defs");
    const gradient = defs.append("linearGradient")
        .attr("id", "gpa-gradient")
        .attr("x1", "0%")
        .attr("y1", "0%")
        .attr("x2", "100%")
        .attr("y2", "0%");

    stops.forEach((stop) => {
        const offset = ((stop.value - min_gpa) / (max_gpa - min_gpa)) * 100;
        gradient.append("stop")
            .attr("offset", `${offset}%`)
            .attr("stop-color", stop.color);
    });

    legendGroup.append("rect")
        .attr("x", 0)
        .attr("y", 0)
        .attr("width", width)
        .attr("height", height)
        .style("fill", "url(#gpa-gradient)");

    // 0 label
    legendGroup.append("text")
        .attr("x", 0)
        .attr("y", height + 15)
        .attr("text-anchor", "middle")
        .style("font-size", "12px")
        .text("0");

    // dynamic_min label
    const dynamicMinX = width * ((dynamic_min - min_gpa) / (max_gpa - min_gpa));
    legendGroup.append("text")
        .attr("x", dynamicMinX)
        .attr("y", height + 15)
        .attr("text-anchor", "middle")
        .style("font-size", "12px")
        .text(dynamic_min.toFixed(1));

    // dynamic_max label
    const dynamicMaxX = width * ((dynamic_max - min_gpa) / (max_gpa - min_gpa));
    legendGroup.append("text")
        .attr("x", dynamicMaxX)
        .attr("y", height + 15)
        .attr("text-anchor", "middle")
        .style("font-size", "12px")
        .text(dynamic_max.toFixed(1));

    // 3 label
    legendGroup.append("text")
        .attr("x", width)
        .attr("y", height + 15)
        .attr("text-anchor", "middle")
        .style("font-size", "12px")
        .text("3");

    // Add labels at clear numbers (1, 2) if not dynamic_min or dynamic_max
    [1, 2].forEach((value) => {
        if (value !== dynamic_min && value !== dynamic_max) {
            const valueX = width * ((value - min_gpa) / (max_gpa - min_gpa));
            legendGroup.append("text")
                .attr("x", valueX)
                .attr("y", height + 15)
                .attr("text-anchor", "middle")
                .style("font-size", "12px")
                .text(value.toString());
        }
    });
    // Add a middle label to describe the legend
    legendGroup.append("text")
    .attr("x", width / 2)
    .attr("y", -10) // Position above the legend gradient
    .attr("text-anchor", "middle")
    .style("font-size", "14px")
    .style("font-weight", "bold")
    .text("Player AMOP Legend");
}

function getContrastColor(hexColor) {
    const r = parseInt(hexColor.substr(1, 2), 16) / 255;
    const g = parseInt(hexColor.substr(3, 2), 16) / 255;
    const b = parseInt(hexColor.substr(5, 2), 16) / 255;

    // This should calculate luminancy according to internet
    const luminance = 0.299 * r + 0.587 * g + 0.114 * b;

    // Return black for light backgrounds, white for dark backgrounds
    return luminance > 0.5 ? "black" : "white";
}