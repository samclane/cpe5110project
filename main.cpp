#include <stdlib.h>
#include <iostream>
#include <stdio.h> 
#include <string>
#include <cstring>
#include <fstream>
#include <vector>
using namespace std;
const int INPUT_BUFFER_SIZE = 10000;


int main (int argc, char** argv)
{
	string inputBuffer[INPUT_BUFFER_SIZE];
	string temp_line;
	int instrCount, memoryCount;
	int index;
	ifstream in_stream;
	if (argc != 2)
	{
		cerr << "Please input a file name" << endl;
		return 0;
	}
	try 
	{
		in_stream.open(argv[1]);
	}
	catch (ifstream::failure e) 
	{
		//never executes
		cerr << "Exception reading/opening file\n";
	}
	while(!in_stream.eof())
	{
		getline(in_stream,temp_line); //gets next line from file
		if (48 <= ((temp_line[0]-'0') + 48) && ((temp_line[0]-'0') + 48) <= 57)
		{
			//first value is a number
			int index2 = 0;
			string tempNum = "";
			while(temp_line[index2] != ' ')
			{
				tempNum += temp_line[index2];
				index2++;
			}
			instrCount = atoi(tempNum.c_str());
			cout << "found int: " << ((temp_line[0]-'0') + 48) << endl;
		} 
		index++;
	}
	in_stream.close();



	for (int i = 0; i < 0; i++)
	{
		cout << inputBuffer[i] << endl;
	}
}


