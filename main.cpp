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
	/* DEBUG SECTION */
	int myCount = 0;
	/* END DEBUG     */

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
		//cout << temp_line[0] << endl;
		//cout << temp_line[0] - '0' << endl;
		if (0 <= (temp_line[0]-'0') && (temp_line[0]-'0') <= 9)
		{
			//if first value is a number
			int line_index = 0;
			string temp_num = "";
			while(temp_line[line_index] != '\n')
			{
				if(temp_line[line_index] == '-')
				{
					cout << "found a - while getting number" << endl;
					if(temp_line[line_index+1] == '-')
					{
						//found an inline comment
						cout << "found a whole comment while getting number\n";
						break;
					}
				}
				temp_num += temp_line[line_index];
				line_index++;
			}
			if (instrCount == -1)
			{
				instrCount = atoi(temp_num.c_str());
			}
			else if (memoryCount == -1)
			{
				memoryCount = atoi(temp_num.c_str());
			}
			else
			{
				cerr << "Found a third number in file. Something is wrong." << endl;
				in_stream.close();
				return 0;
			}
		}
		if ('A' <= (temp_line[0] - '0' + 48) && (temp_line[0] - '0' + 48) <= 'Z')
		{
			//if first value is a character
			int line_index = 0;
			string temp_instruction = "";
			while(temp_line[line_index] != '\n')
			{

				if(temp_line[line_index] == '-')
				{
					cout << "found a - while getting instruction\n";
					if(temp_line[line_index+1] == '-')
					{
						//found an inline comment
						cout << "found a whole coment while getting instruction\n";
						break;
					}
				}
				temp_instruction += temp_line[line_index];
				line_index++;
			}
			cout << temp_instruction << endl;
		} 
		index++;
	}
	in_stream.close();
	cout << "instrCount: " << instrCount << endl;
	cout << "memoryCount: " << memoryCount << endl;
}


