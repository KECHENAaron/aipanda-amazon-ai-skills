import Foundation
import Vision
import AppKit

guard CommandLine.arguments.count == 2 else { exit(2) }
let url = URL(fileURLWithPath: CommandLine.arguments[1])
let request = VNRecognizeTextRequest()
request.recognitionLevel = .accurate
request.recognitionLanguages = ["en-US", "zh-Hans"]
request.usesLanguageCorrection = false
do {
    try VNImageRequestHandler(url: url, options: [:]).perform([request])
    let lines: [[String: Any]] = (request.results ?? []).compactMap { item in
        guard let text = item.topCandidates(1).first else { return nil }
        return ["text": text.string, "confidence": text.confidence,
                "box": [item.boundingBox.minX, item.boundingBox.minY, item.boundingBox.width, item.boundingBox.height]]
    }
    let output = try JSONSerialization.data(withJSONObject: lines, options: [.sortedKeys])
    print(String(data: output, encoding: .utf8)!)
} catch {
    fputs("OCR failed: \(error.localizedDescription)\n", stderr)
    exit(1)
}
