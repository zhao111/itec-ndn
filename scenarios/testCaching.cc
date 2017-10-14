#include "ns3/core-module.h"
#include "ns3/network-module.h"
#include "ns3/ndn-all.hpp"

#include "ns3/ndnSIM/utils/tracers/ndn-dashplayer-tracer.hpp"
#include "../extensions/utils/parameterconfiguration.h"
#include "../extensions/utils/extendedglobalroutinghelper.h"
#include "../extensions/utils/prefixtracer.h"

using namespace ns3;

int main(int argc, char* argv[])
{
	ns3::Config::SetDefault("ns3::PointToPointNetDevice::Mtu", StringValue("4096"));

//	std::string outputFolder = "/home/ndnSIM/zhaoxixi-ndn/output/test1/";
//	fprintf(stderr,outputFolder.c_str());
	std::string outputFolder = "output/";
	std::string strategy = "bestRoute";
//	std::string topologyFile = "topologies/3-consumer.top";
	std::string topologyFile = "topologies/saf_scenario.top";

	CommandLine cmd;
//	cmd.AddValue ("outputFolder", "defines specific output subdir", outputFolder);
	cmd.AddValue ("topology", "path to the required topology file", topologyFile);
	cmd.AddValue ("fw-strategy", "Forwarding Strategy", strategy);
	cmd.Parse (argc, argv);

	AnnotatedTopologyReader topologyReader ("", 5);
	topologyReader.SetFileName (topologyFile);
	topologyReader.Read();

	Ptr<UniformRandomVariable> r = CreateObject<UniformRandomVariable>();
	int simTime = 2880;

	//pharse all nodes
	NodeContainer routers;
	int nodeIndex = 0;
	std::string nodeNamePrefix("Router");
	Ptr<Node> router = Names::Find<Node>(nodeNamePrefix +  boost::lexical_cast<std::string>(nodeIndex++));
	while(router != NULL)
	{
		routers.Add (router);
		router =  Names::Find<Node>(nodeNamePrefix +  boost::lexical_cast<std::string>(nodeIndex++));
	}
	//check # of nodes
	fprintf(stderr,"%d",routers.size());

	nodeIndex = 0;
	nodeNamePrefix = std::string("RouterNet");
	router = Names::Find<Node>(nodeNamePrefix);
	routers.Add (router);
	fprintf(stderr,"%d",routers.size());

	NodeContainer streamers;
	nodeIndex = 0;
	nodeNamePrefix = std::string("Streamer");
	Ptr<Node> streamer = Names::Find<Node>(nodeNamePrefix +  boost::lexical_cast<std::string>(nodeIndex++));
	while(streamer != NULL)
	{
		streamers.Add (streamer);
	  	streamer =  Names::Find<Node>(nodeNamePrefix +  boost::lexical_cast<std::string>(nodeIndex++));
	}
	fprintf(stderr, "Parsed %d Streamers\n", streamers.size ());

	nodeNamePrefix = std::string("Source");
    Ptr<Node> producer = Names::Find<Node>(nodeNamePrefix);
//	for multiple sources
//	NodeContainer source;
//    nodeIndex = 0;
//	source = Names::Find<Node>(nodeNamePrefix);
//	source.Add (source);
//    fprintf(stderr, "Parsed %d VideoSource\n", source.size ());
	
	ns3::ndn::StackHelper ndnHelper;
	ndnHelper.SetOldContentStore("ns3::ndn::cs::Lru", "MaxSize","100"); // default ContentStore parameters

	ndnHelper.Install(routers);
	ndnHelper.Install(streamers);
	ndnHelper.Install(producer);

	ns3::ndn::StrategyChoiceHelper::Install((routers),"/myprefix", "/localhost/nfd/strategy/best-route");
	ns3::ndn::StrategyChoiceHelper::Install((streamers),"/myprefix", "/localhost/nfd/strategy/best-route");
	ns3::ndn::StrategyChoiceHelper::Install((producer),"/myprefix", "/localhost/nfd/strategy/best-route");

	//ParameterConfiguration::getInstance()->setParameter("PREFIX_COMPONENT", 0); // set to prefix componen

	//install consumer
	ns3::ndn::AppHelper consumerVideoHelper("ns3::ndn::FileConsumerCbr::MultimediaConsumer");
	consumerVideoHelper.SetAttribute("AllowUpscale", BooleanValue(true));
	consumerVideoHelper.SetAttribute("AllowDownscale", BooleanValue(false));
	consumerVideoHelper.SetAttribute("ScreenWidth", UintegerValue(1920));
	consumerVideoHelper.SetAttribute("ScreenHeight", UintegerValue(1080));
	consumerVideoHelper.SetAttribute("StartRepresentationId", StringValue("auto"));
	consumerVideoHelper.SetAttribute("AdaptationLogic", StringValue("dash::player::SVCBufferBasedAdaptationLogic"));
	consumerVideoHelper.SetAttribute("MaxBufferedSeconds", UintegerValue(50));
	consumerVideoHelper.SetAttribute("TraceNotDownloadedSegments", BooleanValue(true));
	consumerVideoHelper.SetAttribute("StartUpDelay", DoubleValue(0.1));
	//consumerVideoHelper.SetAttribute ("LifeTime", StringValue("1s"));

	std::string mpd("/myprefix/SVC/BBB-III.mpd");
	consumerVideoHelper.SetAttribute("MpdFileToRequest", StringValue(mpd.c_str()));

	for(int i=0; i<streamers.size (); i++)
	{
		ApplicationContainer consumer = consumerVideoHelper.Install (streamers.Get (i));
		consumer.Start (Seconds(r->GetInteger (0,3)));
		consumer.Stop (Seconds(simTime));
//		ns3::ndn::L3RateTracer::Install (streamers.Get (i), std::string(outputFolder +"/consumer_aggregate-trace_"+boost::lexical_cast<std::string>(i)).append(".txt"), Seconds (simTime));
		ns3::ndn::DASHPlayerTracer::Install (streamers.Get (i), std::string(outputFolder +"/consumer_dash-trace_"+boost::lexical_cast<std::string>(i)).append(".txt"));
//		ns3::ndn::CsTracer::Install (streamers.Get (i), std::string(outputFolder +"/consumer_cs-trace_"+boost::lexical_cast<std::string>(i)).append(".txt"));
	}
	
	//install global routing interface on all nodes
	ns3::ndn::ExtendedGlobalRoutingHelper ndnGlobalRoutingHelper;
	ndnGlobalRoutingHelper.InstallAll();
	
	//install producer application on the provider
	ns3::ndn::AppHelper videoProducerHelper ("ns3::ndn::FileServer");
 	videoProducerHelper.SetPrefix("/myprefix");
	videoProducerHelper.SetAttribute("ContentDirectory", StringValue("/home/someuser/multimediaData/"));

	videoProducerHelper.Install(producer);
	ndnGlobalRoutingHelper.AddOrigins("/myprefix",producer);

	ns3::ndn::GlobalRoutingHelper::CalculateAllPossibleRoutes ();
//	for(int i=0; i<routers.size();i++)
//	{
//		ns3::ndn::CsTracer::Install(routers.Get (i), std::string(outputFolder +"/cs-trace_" + boost::lexical_cast<std::string>(i)).append(".txt"));
//		ns3::ndn::DASHPlayerTracer::Install(routers.Get (i), std::string(outputFolder +"/dash-trace_" + boost::lexical_cast<std::string>(i)).append(".txt"));	
//		ns3::ndn::L3RateTracer::Install(routers.Get (i), std::string(outputFolder +"/rate-trace_" + boost::lexical_cast<std::string>(i)).append(".txt"));
//	}	
//	ns3::ndn::CsTracer::InstallAll("./output/test1/cs-trace.txt", Seconds(1));
//	ns3::ndn::DASHPlayerTracer::InstallAll("./output/test1/dash-output.txt");
//	ns3::ndn::L3RateTracer::InstallAll("./output/test1/rate-output.txt");
	Simulator::Stop (Seconds(simTime+1));
	Simulator::Run();
	Simulator::Destroy();

	NS_LOG_UNCOND("Simulation Finished.");
	return 0;
}

