#include "ns3/core-module.h"
#include "ns3/network-module.h"
#include "ns3/point-to-point-module.h"
#include "ns3/point-to-point-layout-module.h"
#include "ns3/ndn-all.hpp"

#include "ns3-dev/ns3/ndnSIM/utils/tracers/ndn-l3-tracer.hpp"
#include "ns3-dev/ns3/ndnSIM/utils/tracers/ndn-app-delay-tracer.hpp"
#include "ns3-dev/ns3/ndnSIM/utils/tracers/ndn-cs-tracer.hpp"
#include "ns3/ndnSIM/utils/tracers/ndn-dashplayer-tracer.hpp"

#include "../extensions/randnetworks/networkgenerator.h"
#include "../extensions/utils/parameterconfiguration.h"
#include "../extensions/utils/extendedglobalroutinghelper.h"
#include "../extensions/utils/prefixtracer.h"
#include <fstream>
#include <string>
#include "ns3/drop-tail-queue.h"

using namespace ns3;

typedef std::map<int /*client*/,int /*server*/> ClientServerPairs;

int main(int argc, char *argv[])
{
//	ns3::Config::SetDefault("ns3::PointToPointNetDevice::Mtu", StringValue("4096"));

	std::string confFile = "/home/ndnSIM/zhaoxixi-ndn/topologies/jsac.top";
//    std::string confFile = "/home/ndnSIM/zhaoxixi-ndn/comsoc_tops/LowBW_HighCon_2.top";
  	std::string strategy = "bestRoute";
  	std::string route = "all";
  	std::string outputFolder = "output/";
  	std::string content_popularity = "uniform";
	
	CommandLine cmd;
	cmd.AddValue ("configFile", "BRITE conf file", confFile);
	cmd.AddValue ("fw-strategy", "Forwarding Strategy", strategy);
  	cmd.AddValue ("route", "defines if you use a single route or all possible routes", route);
  	cmd.AddValue ("outputFolder", "defines specific output subdir", outputFolder);
  	cmd.AddValue ("content-popularity", "Defines the model for the content popularity", content_popularity);

	cmd.Parse (argc, argv);
	
	//parse comsoc topology (quick and dirty..)
  	std::ifstream file(confFile);
//	fprintf(stderr, "confFile: %s\n", confFile.c_str());
  	std::string line;

  	Config::SetDefault ("ns3::RateErrorModel::ErrorRate", DoubleValue (0.00));
  	Config::SetDefault ("ns3::RateErrorModel::ErrorUnit", StringValue ("ERROR_UNIT_PACKET"));
	
	std::getline(file,line);
//	fprintf(stderr, "line: %s\n", line.c_str());
  	if(!boost::starts_with(line,"#number of nodes"))
	{
    	fprintf(stderr, "1 Invalid jsac topolgy!\n");
    	exit(0);
  	}

  	int nr_nodes = 0;
  	std::getline(file,line);
  	nr_nodes = boost::lexical_cast<int>(line);

  	fprintf(stderr, "JsacTop: %d nodes\n",nr_nodes);

	std::getline(file,line);
  	if(!boost::starts_with(line,"#nodes (n1,n2,bandwidth in bits)"))
  	{
    	fprintf(stderr, "2 Invalid jsac topolgy!\n");
    	exit(0);
  	}

	NodeContainer nodes;
  	ClientServerPairs pairs;

  	nodes.Create (nr_nodes);

  	for(int i=0; i<nodes.size (); i++)
  	{
    	Names::Add (std::string("Node_" + boost::lexical_cast<std::string>(i)), nodes.Get (i));
  	}

  	PointToPointHelper *p2p = new PointToPointHelper;

  	std::getline(file,line);
  	std::vector<std::string> attributes;
  	int n1, n2, bw;

	ObjectFactory m_queueFactory;
   	ObjectFactory m_channelFactory;
   	ObjectFactory m_deviceFactory;
   	m_queueFactory.SetTypeId ("ns3::DropTailQueue");
   	m_deviceFactory.SetTypeId ("ns3::PointToPointNetDevice");
   	m_channelFactory.SetTypeId ("ns3::PointToPointChannel");

	while(!boost::starts_with(line, "#properties (Client, Server)")) // create the connections
  	{
    //	fprintf(stderr, "properties line: %s\n", line.c_str());
		boost::split(attributes, line, boost::is_any_of(","));

    	if(attributes.size () < 3)
    	{
      		fprintf(stderr,"Invalid Link Specification\n");
      		exit(0);
    	}

    	n1 = boost::lexical_cast<int>(attributes.at (0));
    	n2 = boost::lexical_cast<int>(attributes.at (1));
    	bw = boost::lexical_cast<int>(attributes.at (2));
		
	//	m_channelFactory.Set ("Delay", 0);

		std::string rate = boost::lexical_cast<std::string>(bw);
    	rate = rate.append ("kbps");
    	m_deviceFactory.Set ("DataRate", StringValue(rate));

		Ptr<Node> a = nodes.Get (n1);
    	Ptr<Node> b = nodes.Get (n2);

    	Ptr<PointToPointNetDevice> devA = m_deviceFactory.Create<PointToPointNetDevice> ();
    	devA->SetAddress (Mac48Address::Allocate ());
    	a->AddDevice (devA);

		std::string queueSizeBytes = boost::lexical_cast<std::string>(bw *1000/8/10);//set queue size to 100ms
    	fprintf(stderr, "queueSizeBytes =%s for rate %s kbps\n", queueSizeBytes.c_str (), rate.c_str ());
    	Ptr<Queue> queueA = m_queueFactory.Create<DropTailQueue> ();
    	queueA->SetAttribute ("Mode",StringValue("QUEUE_MODE_BYTES"));
    	queueA->SetAttribute ("MaxBytes", StringValue(queueSizeBytes));
    	devA->SetQueue (queueA);

		Ptr<PointToPointNetDevice> devB = m_deviceFactory.Create<PointToPointNetDevice> ();
    	devB->SetAddress (Mac48Address::Allocate ());
    	b->AddDevice (devB);
    	Ptr<Queue> queueB = m_queueFactory.Create<DropTailQueue> ();
    	queueSizeBytes = boost::lexical_cast<std::string>(bw *1000/8/10);//set queue size to 100ms
    	queueB->SetAttribute ("Mode",StringValue("QUEUE_MODE_BYTES"));
    	queueB->SetAttribute ("MaxBytes", StringValue(queueSizeBytes));
    	devB->SetQueue (queueB);

		Ptr<PointToPointChannel> channel = m_channelFactory.Create<PointToPointChannel> ();
    	devA->Attach (channel);
    	devB->Attach (channel);

    	std::getline(file,line);
	}

	if(!boost::starts_with(line,"#properties (Client, Server)"))
  	{
    	fprintf(stderr, "Invalid jsac topolgy!\n");
    	exit(0);
  	}

  	std::getline(file,line);
  	int c_id = 0, s_id = 0;

  	while(!boost::starts_with(line, "#eof //do not delete this")) // server/clients nodes
  	{
    //	fprintf(stderr, "server/clients line: %s\n", line.c_str());
		boost::split(attributes, line, boost::is_any_of(","));

    	if(attributes.size () < 2)
    	{
      		fprintf(stderr,"Invalid Properties Specification\n");
      		exit(0);
    	}
    	c_id = boost::lexical_cast<int>(attributes.at (0));
    	s_id = boost::lexical_cast<int>(attributes.at (1));
    	pairs[c_id] = s_id;

    	std::getline(file,line);
  	}

	fprintf(stderr,"Pairs:\n");
  	for(ClientServerPairs::iterator it = pairs.begin (); it != pairs.end (); it++)
    	fprintf(stderr, "(%d,%d)\n", it->first, it->second);

	//int simTime = 2880;
	int simTime = 60;

	ns3::ndn::StackHelper ndnHelper;
	ndnHelper.SetOldContentStore("ns3::ndn::cs::Lru", "MaxSize","100"); // default ContentStore parameters
//	ndnHelper.SetOldContentStore ("ns3::ndn::cs::Fifo","MaxSize", "65536"); // cache size 250 MB assuming 2kb large video packets
	ndnHelper.Install(nodes);

	//install cstore tracers
 	ns3::ndn::CsTracer::Install(nodes, std::string(outputFolder + "/cs-trace.txt"), Seconds(1.0));

  	ns3::ndn::ExtendedGlobalRoutingHelper ndnGlobalRoutingHelper;
  	ndnGlobalRoutingHelper.InstallAll ();
	
	//install producer
  	std::vector<int> producers_already_seen;
	ns3::ndn::AppHelper producerHelper ("ns3::ndn::FileServer");
    producerHelper.SetPrefix("/myprefix");
    producerHelper.SetAttribute("ContentDirectory", StringValue("/home/someuser/multimediaData/"));	
	producerHelper.SetAttribute ("Freshness", StringValue("300s"));

	//install consumer
	ns3::ndn::AppHelper consumerHelper("ns3::ndn::FileConsumerCbr::MultimediaConsumer");
 	consumerHelper.SetAttribute("AllowUpscale", BooleanValue(true));
	consumerHelper.SetAttribute("AllowDownscale", BooleanValue(false));
	consumerHelper.SetAttribute("ScreenWidth", UintegerValue(1920));
	consumerHelper.SetAttribute("ScreenHeight", UintegerValue(1080));
	consumerHelper.SetAttribute("StartRepresentationId", StringValue("auto"));
	consumerHelper.SetAttribute("AdaptationLogic", StringValue("dash::player::SVCBufferBasedAdaptationLogic"));
	consumerHelper.SetAttribute("MaxBufferedSeconds", UintegerValue(50));
	consumerHelper.SetAttribute("TraceNotDownloadedSegments", BooleanValue(true));
	consumerHelper.SetAttribute("StartUpDelay", DoubleValue(0.1));
  	consumerHelper.SetAttribute ("LifeTime", StringValue("1s"));
	
	std::string mpd("/myprefix/SVC/BBB-III.mpd");
	consumerHelper.SetAttribute("MpdFileToRequest", StringValue(mpd.c_str()));

	Ptr<UniformRandomVariable> r = CreateObject<UniformRandomVariable>();
  	r->SetAttribute ("Min", DoubleValue (0));
  	r->SetAttribute ("Max", DoubleValue (1));
	
	for(ClientServerPairs::iterator it = pairs.begin (); it != pairs.end (); it++)
  	{
    	//fprintf(stderr, "(%d,%d)\n", it->first, it->second);

    	c_id = it->first;
    	s_id = it->second;

    	if(std::find(producers_already_seen.begin (), producers_already_seen.end (), s_id) == producers_already_seen.end ())
    	{
      	//	producerHelper.SetPrefix (std::string("/Server_" + boost::lexical_cast<std::string>(s_id)));
      		producerHelper.Install (nodes.Get (s_id));
      		ndnGlobalRoutingHelper.AddOrigins("/myprefix",nodes.Get(s_id));
		//	ndnGlobalRoutingHelper.AddOrigin(std::string("/Server_" + boost::lexical_cast<std::string>(s_id)),nodes.Get (s_id));
      		ns3::ndn::L3RateTracer::Install (nodes.Get (s_id), std::string(outputFolder + "/server_aggregate-trace_"  + boost::lexical_cast<std::string>(s_id)).append(".txt"), Seconds (simTime));
      		producers_already_seen.push_back (s_id);
    	}

    //	consumerHelper.SetPrefix (std::string("/Server_" + boost::lexical_cast<std::string>(s_id)));
    	ApplicationContainer consumer = consumerHelper.Install (nodes.Get (c_id));
    	consumer.Start (Seconds(r->GetValue()*5.0));
    	consumer.Stop (Seconds(simTime));

    	ns3::ndn::L3RateTracer::Install (nodes.Get (c_id), std::string(outputFolder + "/consumer_aggregate-trace_"  + boost::lexical_cast<std::string>(c_id)).append(".txt"), Seconds (simTime));
   		ns3::ndn::L3RateTracer::Install (nodes.Get (c_id), std::string(outputFolder + "/consumer_dash-trace_"  + boost::lexical_cast<std::string>(c_id)).append(".txt"), Seconds (simTime)); 
	    ns3::ndn::AppDelayTracer::Install(nodes.Get (c_id), std::string(outputFolder +"/consumer_app-delays-trace_"  + boost::lexical_cast<std::string>(c_id)).append(".txt"));
	}

	bool isRouter;
  	for(int index = 0; index < nodes.size (); index++)
  	{
    	bool isRouter = true;
    	for(ClientServerPairs::iterator it = pairs.begin (); it != pairs.end (); it++)
    	{
      		if(it->first == index || it->second == index)
      		{
        		isRouter = false;
        		break;
      		}
    	}
    	if(isRouter)
    	{
      		ns3::ndn::L3RateTracer::Install (nodes.Get (index), std::string(outputFolder + "/router_aggregate-trace_"  + boost::lexical_cast<std::string>(index)).append(".txt"), Seconds (simTime));
    	}
  	}

	// Calculate and install FIBs
  	if(route.compare ("all") == 0)
    	ns3::ndn::GlobalRoutingHelper::CalculateAllPossibleRoutes ();
  	else if(route.compare ("single") == 0)
    	ns3::ndn::GlobalRoutingHelper::CalculateRoutes ();
  	else
  	{
    	fprintf(stderr, "Invalid routing algorithm\n");
    	exit(-1);
  	}

	Simulator::Stop (Seconds(simTime+1));
	Simulator::Run();
	Simulator::Destroy();

	NS_LOG_UNCOND("Simulation Finished.");
	return 0;
}

