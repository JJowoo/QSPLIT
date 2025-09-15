import 'package:flutter/material.dart';

class CodeLayer extends StatelessWidget {
  final String selectedLayer;
  final Function(String) onChanged;

  const CodeLayer({
    super.key,
    required this.selectedLayer,
    required this.onChanged,
  });

  @override
  Widget build(BuildContext context) {
    final layers = [
      'GeneralEncoder',
      'StateEncoder',
      'PhaseEncoder',
      'MultiphaseEncoder',
      'MagnitudeEncoder'
    ];

    return Container(
      constraints:
          const BoxConstraints(minHeight: 360), // HyperparameterConfig와 높이 맞춤
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: Colors.white.withOpacity(0.05),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: Colors.grey.shade600),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Center(
            child: Text(
              'Target Code Layer',
              style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold),
            ),
          ),
          const SizedBox(height: 12),
          Container(
            height: 280, // 높이 늘림
            decoration: BoxDecoration(
              color: Colors.blueGrey.shade800.withOpacity(0.4),
              borderRadius: BorderRadius.circular(10),
            ),
            child: ListView(
              padding: const EdgeInsets.all(8),
              children: layers.map((layer) {
                return RadioListTile<String>(
                  title: Text(layer),
                  value: layer,
                  groupValue: selectedLayer,
                  onChanged: (val) => onChanged(val!),
                );
              }).toList(),
            ),
          ),
        ],
      ),
    );
  }
}
