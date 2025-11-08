import { useState } from 'react';
import { Play, CheckCircle, Timer, Lightbulb, BookOpen, ArrowLeft } from 'lucide-react';
import { Card } from '../ui/card';
import { Button } from '../ui/button';
import { Badge } from '../ui/badge';
import { Textarea } from '../ui/textarea';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../ui/tabs';

const problem = {
  title: 'Two Sum',
  difficulty: 'Easy',
  topic: 'Arrays & Hashing',
  xp: 30,
  description: `Given an array of integers nums and an integer target, return indices of the two numbers such that they add up to target.

You may assume that each input would have exactly one solution, and you may not use the same element twice.

You can return the answer in any order.`,
  examples: [
    {
      input: 'nums = [2,7,11,15], target = 9',
      output: '[0,1]',
      explanation: 'Because nums[0] + nums[1] == 9, we return [0, 1].'
    },
    {
      input: 'nums = [3,2,4], target = 6',
      output: '[1,2]',
      explanation: 'Because nums[1] + nums[2] == 6, we return [1, 2].'
    }
  ],
  constraints: [
    '2 <= nums.length <= 10^4',
    '-10^9 <= nums[i] <= 10^9',
    '-10^9 <= target <= 10^9',
    'Only one valid answer exists.'
  ],
  starterCode: `def twoSum(nums, target):
    """
    :type nums: List[int]
    :type target: int
    :rtype: List[int]
    """
    # Write your solution here
    pass`
};

const testCases = [
  { input: 'nums = [2,7,11,15], target = 9', expected: '[0,1]', status: 'pending' },
  { input: 'nums = [3,2,4], target = 6', expected: '[1,2]', status: 'pending' },
  { input: 'nums = [3,3], target = 6', expected: '[0,1]', status: 'pending' },
];

export function CodingPracticeMockup() {
  const [code, setCode] = useState(problem.starterCode);
  const [timeElapsed, setTimeElapsed] = useState(0);
  const [isRunning, setIsRunning] = useState(false);

  return (
    <div className="min-h-screen bg-slate-900">
      {/* Header */}
      <header className="bg-slate-800 border-b border-slate-700 px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Button variant="ghost" className="text-slate-300 hover:text-white">
              <ArrowLeft className="w-4 h-4 mr-2" />
              Back to Plan
            </Button>
            <div className="h-6 w-px bg-slate-600"></div>
            <h1 className="text-white text-xl">{problem.title}</h1>
            <Badge className={
              problem.difficulty === 'Easy' ? 'bg-green-500' :
              problem.difficulty === 'Medium' ? 'bg-yellow-500' :
              'bg-red-500'
            }>
              {problem.difficulty}
            </Badge>
            <Badge variant="outline" className="text-slate-300 border-slate-600">
              {problem.topic}
            </Badge>
          </div>
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2 text-slate-300">
              <Timer className="w-4 h-4" />
              <span>{Math.floor(timeElapsed / 60)}:{(timeElapsed % 60).toString().padStart(2, '0')}</span>
            </div>
            <Badge className="bg-purple-600">+{problem.xp} XP</Badge>
          </div>
        </div>
      </header>

      <div className="grid grid-cols-2 h-[calc(100vh-73px)]">
        {/* Left Panel - Problem Description */}
        <div className="bg-slate-800 border-r border-slate-700 overflow-y-auto">
          <div className="p-6">
            <Tabs defaultValue="description" className="w-full">
              <TabsList className="bg-slate-900 mb-4">
                <TabsTrigger value="description">Description</TabsTrigger>
                <TabsTrigger value="hints">Hints</TabsTrigger>
                <TabsTrigger value="solutions">Solutions</TabsTrigger>
              </TabsList>

              <TabsContent value="description" className="space-y-6">
                <div>
                  <h2 className="text-white text-lg mb-3">Problem Description</h2>
                  <p className="text-slate-300 whitespace-pre-line">{problem.description}</p>
                </div>

                <div>
                  <h3 className="text-white mb-3">Examples</h3>
                  {problem.examples.map((example, index) => (
                    <Card key={index} className="p-4 bg-slate-900 border-slate-700 mb-3">
                      <div className="text-sm space-y-2">
                        <div>
                          <span className="text-slate-400">Input:</span>
                          <code className="ml-2 text-green-400">{example.input}</code>
                        </div>
                        <div>
                          <span className="text-slate-400">Output:</span>
                          <code className="ml-2 text-blue-400">{example.output}</code>
                        </div>
                        <div className="text-slate-400">
                          <span>Explanation:</span> <span className="text-slate-300">{example.explanation}</span>
                        </div>
                      </div>
                    </Card>
                  ))}
                </div>

                <div>
                  <h3 className="text-white mb-3">Constraints</h3>
                  <ul className="space-y-2">
                    {problem.constraints.map((constraint, index) => (
                      <li key={index} className="text-slate-300 text-sm">• {constraint}</li>
                    ))}
                  </ul>
                </div>
              </TabsContent>

              <TabsContent value="hints">
                <Card className="p-4 bg-slate-900 border-slate-700">
                  <div className="flex items-start gap-3">
                    <Lightbulb className="w-5 h-5 text-yellow-500 mt-1" />
                    <div>
                      <h3 className="text-white mb-2">Hint 1</h3>
                      <p className="text-slate-300 text-sm">
                        Try using a hash map to store numbers you've seen and their indices.
                      </p>
                    </div>
                  </div>
                </Card>
                <Card className="p-4 bg-slate-900 border-slate-700 mt-3">
                  <div className="flex items-start gap-3">
                    <Lightbulb className="w-5 h-5 text-yellow-500 mt-1" />
                    <div>
                      <h3 className="text-white mb-2">Hint 2</h3>
                      <p className="text-slate-300 text-sm">
                        For each number, check if (target - current number) exists in your hash map.
                      </p>
                    </div>
                  </div>
                </Card>
              </TabsContent>

              <TabsContent value="solutions">
                <Card className="p-4 bg-slate-900 border-slate-700">
                  <div className="flex items-start gap-3 mb-4">
                    <BookOpen className="w-5 h-5 text-blue-500 mt-1" />
                    <div>
                      <h3 className="text-white mb-2">Hash Map Approach</h3>
                      <p className="text-slate-300 text-sm mb-3">
                        Use a dictionary to store values and their indices as you iterate through the array.
                      </p>
                    </div>
                  </div>
                  <div className="bg-slate-950 rounded p-4 border border-slate-700">
                    <code className="text-sm text-green-400">
                      <pre>{`def twoSum(nums, target):
    seen = {}
    for i, num in enumerate(nums):
        complement = target - num
        if complement in seen:
            return [seen[complement], i]
        seen[num] = i
    return []`}</pre>
                    </code>
                  </div>
                  <div className="mt-3 text-sm text-slate-400">
                    Time Complexity: O(n) • Space Complexity: O(n)
                  </div>
                </Card>
              </TabsContent>
            </Tabs>
          </div>
        </div>

        {/* Right Panel - Code Editor */}
        <div className="bg-slate-900 flex flex-col">
          <div className="p-4 border-b border-slate-700">
            <div className="flex items-center justify-between mb-2">
              <span className="text-slate-300 text-sm">Python 3</span>
              <div className="flex gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  className="bg-slate-800 text-slate-300 border-slate-600 hover:bg-slate-700"
                  onClick={() => setIsRunning(true)}
                >
                  <Play className="w-4 h-4 mr-2" />
                  Run Code
                </Button>
                <Button
                  size="sm"
                  className="bg-green-600 hover:bg-green-700"
                >
                  <CheckCircle className="w-4 h-4 mr-2" />
                  Submit
                </Button>
              </div>
            </div>
          </div>

          <Textarea
            value={code}
            onChange={(e) => setCode(e.target.value)}
            className="flex-1 bg-slate-950 text-green-400 font-mono text-sm border-0 rounded-none resize-none focus-visible:ring-0 p-4"
            style={{ minHeight: '400px' }}
          />

          {/* Test Cases */}
          <div className="border-t border-slate-700 bg-slate-800 p-4">
            <h3 className="text-white mb-3">Test Cases</h3>
            <div className="space-y-2">
              {testCases.map((test, index) => (
                <Card key={index} className="p-3 bg-slate-900 border-slate-700">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="text-sm text-slate-300 mb-1">
                        <span className="text-slate-400">Input:</span> {test.input}
                      </div>
                      <div className="text-sm text-slate-300">
                        <span className="text-slate-400">Expected:</span> {test.expected}
                      </div>
                    </div>
                    {isRunning && (
                      <Badge className="bg-green-600">Passed</Badge>
                    )}
                  </div>
                </Card>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
