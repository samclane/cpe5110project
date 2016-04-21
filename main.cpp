#include <stdlib.h>
#include <iostream>
#include <stdio.h> 
#include <string>
#include <cstring>
#include <fstream>
#include <vector>
using namespace std;


int main (int argc, char** argv)
{
	string temp_line;
	int instrCount = -1, memoryCount = -1;
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
			//if first value is a number
			int line_index = 0;
			string tempNum = "";
			while(temp_line[line_index] != ' ')
			{
				tempNum += temp_line[line_index];
				line_index++;
			}
			if (instrCount == -1)
			{
				instrCount = atoi(tempNum.c_str());
			}
			else if (memoryCount == -1)
			{
				memoryCount = atoi(tempNum.c_str());
			}
			else
			{
				cerr << "Found a third number in file. Something is wrong." << endl;
				in_stream.close();
				return 0;
			}
		} 
		index++;
	}
	in_stream.close();
	cout << "instrCount: " << instrCount << endl;
	cout << "memoryCount: " << memoryCount << endl;
}


