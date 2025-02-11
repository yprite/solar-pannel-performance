function processData(solarArray) {
    var solarDict = {};
    solarArray.forEach(entry => {
        solarDict[entry.Location] = entry;
    });
    return solarDict;
}

var processedSolarData = processData(solarData);

var width = 800, height = 600;
var svg = d3.select("#map")
    .attr("width", width)
    .attr("height", height);

var projection = d3.geoMercator().fitSize([width, height], geoJsonData);
var path = d3.geoPath().projection(projection);

var g = svg.append("g");

var colorScale = d3.scaleLinear()
    .domain([3.7, 4.0, 4.3])  // 3.5~4.5 범위로 조정
    .range(["blue", "yellow", "red"]);  // 색상 차이를 더 강조

g.selectAll(".region")
    .data(geoJsonData.features)
    .enter().append("path")
    .attr("class", "region")
    .attr("d", path)
    .attr("fill", function (d) {
        var regionName = d.properties.adm_nm;
        return processedSolarData[regionName] ? colorScale(d3.mean(Object.values(processedSolarData[regionName]).slice(0, 12))) : "#f0f0f0";
    })
    .on("click", function (event, d) {
        showTooltip(event, d);
    });

var zoom = d3.zoom()
    .scaleExtent([1, 8])
    .on("zoom", function (event) {
        g.attr("transform", event.transform);
    });

svg.call(zoom);

function resetZoom() {
    svg.transition().duration(750).call(
        zoom.transform,
        d3.zoomIdentity
    );
    d3.select("#tooltip").style("opacity", 0);
}

function showTooltip(event, d) {
    var regionName = d.properties.adm_nm;

    var bounds = path.bounds(d);
    var dx = bounds[1][0] - bounds[0][0];
    var dy = bounds[1][1] - bounds[0][1];
    var x = (bounds[0][0] + bounds[1][0]) / 2;
    var y = (bounds[0][1] + bounds[1][1]) / 2;
    var scale = Math.max(1, Math.min(8, 0.9 / Math.max(dx / width, dy / height)));
    var translateX = width / 2 - scale * x;
    var translateY = height / 2 - scale * y;

    // 지도 중심 이동
    svg.transition().duration(750).call(
        zoom.transform,
        d3.zoomIdentity.translate(translateX, translateY).scale(scale)
    );

    // 툴팁 표시
    if (processedSolarData[regionName]) {
        var solarValues = Object.values(processedSolarData[regionName]).slice(0, 12).map(Number);
        var avgValue = (solarValues.reduce((a, b) => a + b, 0) / solarValues.length).toFixed(2);
        var months = ["1월", "2월", "3월", "4월", "5월", "6월", "7월", "8월", "9월", "10월", "11월", "12월"];

        var maxVal = Math.max(...solarValues);
        var chartHtml = `<svg width='320' height='180'>`;
        chartHtml += `<line x1='40' y1='20' x2='40' y2='150' stroke='#ccc' stroke-width='1'/>`; // Y축
        chartHtml += `<line x1='40' y1='150' x2='300' y2='150' stroke='#ccc' stroke-width='1'/>`; // X축

        // Y축 눈금 및 레이블 추가
        for (let i = 0; i <= maxVal; i += 1) {
            let yPos = 150 - (i / maxVal) * 130;
            chartHtml += `<line x1='35' y1='${yPos}' x2='40' y2='${yPos}' stroke='#999' stroke-width='1'/>`;
            chartHtml += `<text x='30' y='${yPos + 4}' font-size='10' text-anchor='end' fill='#555'>${i}</text>`;
        }

        // 막대그래프 추가
        solarValues.forEach((val, i) => {
            let barHeight = (val / maxVal) * 130;
            chartHtml += `<rect x='${50 + i * 20}' y='${150 - barHeight}' width='15' height='${barHeight}' fill='steelblue'></rect>`;
            chartHtml += `<text x='${58 + i * 20}' y='160' font-size='10' text-anchor='middle' fill='#555'>${months[i]}</text>`; // X축 레이블
        });

        chartHtml += `</svg>`;

        d3.select("#tooltip").style("opacity", 1)
            .style("top", "10px")  
            .style("right", "10px") 
            .html(`<strong>${regionName} (2024년 기준)</strong><br> 평균 발전량: ${avgValue} kWh/m²/day <br>` + chartHtml);
    }
}

var regionList = d3.select("#region-list");
geoJsonData.features.forEach(feature => {
    regionList.append("div")
        .attr("class", "region-item")
        .text(feature.properties.adm_nm)
        .on("click", function () {
            var event = new Event("click");
            d3.selectAll(".region").filter(d => d.properties.adm_nm === feature.properties.adm_nm).dispatch("click", { detail: event });
        });
});