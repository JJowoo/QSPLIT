// log_panel.dart
import 'package:flutter/material.dart';

class LogPanel extends StatelessWidget {
  final List<String> log;

  const LogPanel({
    super.key,
    required this.log,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      color: Colors.black54,
      padding: const EdgeInsets.all(10),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch, // To make Center work
        children: [
          const Center(
            child: Text(
              'Log',
              style: TextStyle(
                fontSize: 18,
                fontWeight: FontWeight.bold,
                color: Colors.white,
              ),
            ),
          ),
          const SizedBox(height: 8),
          const Divider(color: Colors.white54),
          Expanded(
            child: ListView(
              children: log
                  .map((entry) => Text(
                        entry,
                        style: const TextStyle(fontSize: 12, color: Colors.white),
                      ))
                  .toList(),
            ),
          ),
        ],
      ),
    );
  }
}
