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
	/* END DEBUG     */

	string temp_line;
	int instrCount = -1, memoryCount = -1;
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
		if (0 <= (temp_line[0]-'0') && (temp_line[0]-'0') <= 9)
		{
			//if first value is a number
			int line_index = 0;
			string temp_num = "";
			bool commentfound = false;
			while(temp_line[line_index] != '\n' && commentfound == false)
			{
				if(temp_line[line_index] == '-')
				{
					if(temp_line[line_index+1] == '-')
					{
						//found an inline comment
						commentfound = true;
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
			bool commentfound = false;
			while(temp_line[line_index] != '\n' && commentfound == false)
			{
				if(temp_line[line_index] == '-')
				{
					if(temp_line[line_index+1] == '-')
					{
						//found an inline comment
						commentfound = true;
					}
				}
				if (commentfound == false)
				{
					temp_instruction += temp_line[line_index];		
				}
				line_index++;
			}
			cout << temp_instruction << endl;
			temp_line = "";
		}
	}
	in_stream.close();
	cout << "instrCount: " << instrCount << endl;
	cout << "memoryCount: " << memoryCount << endl;
}


